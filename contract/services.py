import json

from copy import copy

from django.core.exceptions import ValidationError

from .config import get_message_counter_contract

from django.db.models.query import Q
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.serializers.json import DjangoJSONEncoder
from django.core.mail import send_mail, BadHeaderError
from django.forms.models import model_to_dict

from contract.apps import ContractConfig
from contract.signals import signal_contract, signal_contract_approve
from contract.models import Contract as ContractModel, \
    ContractDetails as ContractDetailsModel, \
    ContractContributionPlanDetails as ContractContributionPlanDetailsModel
from calculation.services import run_calculation_rules

from policyholder.models import PolicyHolderInsuree
from contribution.models import Premium
from contribution_plan.models import ContributionPlanBundleDetails, ContributionPlan

from policy.models import Policy
from payment.models import Payment, PaymentDetail
from payment.services import update_or_create_payment
from insuree.models import Insuree

from dateutil.relativedelta import relativedelta

from core.signals import *

import logging

logger = logging.getLogger(__file__)


class ContractUpdateError(Exception):

    def __init__(self, msg=None):
        self.msg = msg

    def __str__(self):
        return f"ContractUpdateError: {self.msg}"


def check_authentication(function):
    def wrapper(self, *args, **kwargs):
        if type(self.user) is AnonymousUser or not self.user.id:
            return {
                "success": False,
                "message": "Authentication required",
                "detail": "PermissionDenied",
            }
        else:
            result = function(self, *args, **kwargs)
            return result

    return wrapper


class Contract(object):

    def __init__(self, user):
        self.user = user

    @check_authentication
    def create(self, contract):
        try:
            incoming_code = contract.get('code')
            if check_unique_code(incoming_code):
                raise ValidationError(("Contract code %s already exists" % incoming_code))
            if not self.user.has_perms(ContractConfig.gql_mutation_create_contract_perms):
                raise PermissionError("Unauthorized")
            c = ContractModel(**contract)
            c.state = ContractModel.STATE_DRAFT
            c.save(username=self.user.username)
            uuid_string = f"{c.id}"
            # check if the PH is set
            if "policy_holder_id" in contract:
                # run services updateFromPHInsuree and Contract Valuation
                cd = ContractDetails(user=self.user)
                result_ph_insuree = cd.update_from_ph_insuree(contract_details={
                    "policy_holder_id": contract["policy_holder_id"],
                    "contract_id": uuid_string,
                    "amendment": 0,
                })
                total_amount = self.evaluate_contract_valuation(
                    contract_details_result=result_ph_insuree,
                )["total_amount"]
                c.amount_notified = total_amount
            historical_record = c.history.all().last()
            c.json_ext = _save_json_external(
                user_id=str(historical_record.user_updated.id),
                datetime=str(historical_record.date_updated),
                message=f"create contract status {historical_record.state}"
            )
            c.save(username=self.user.username)
            dict_representation = model_to_dict(c)
            dict_representation['id'], dict_representation['uuid'] = (str(uuid_string), str(uuid_string))
        except Exception as exc:
            return _output_exception(model_name="Contract", method="create", exception=exc)
        return _output_result_success(dict_representation=dict_representation)

    def evaluate_contract_valuation(self, contract_details_result, save=False):
        ccpd = ContractContributionPlanDetails(user=self.user)
        result_contract_valuation = ccpd.contract_valuation(
            contract_contribution_plan_details={
                "contract_details": contract_details_result["data"],
                "save": save,
            }
        )
        if not result_contract_valuation or result_contract_valuation["success"] is False:
            logger.error("contract valuation failed %s", str(result_contract_valuation))
            raise Exception("contract valuation failed " + str(result_contract_valuation))
        return result_contract_valuation["data"]

    # TODO update contract scenario according to wiki page
    @check_authentication
    def update(self, contract):
        try:
            # check rights for contract / amendments
            if not (self.user.has_perms(ContractConfig.gql_mutation_update_contract_perms) or self.user.has_perms(
                    ContractConfig.gql_mutation_approve_ask_for_change_contract_perms)):
                raise PermissionError("Unauthorized")
            updated_contract = ContractModel.objects.filter(id=contract['id']).first()
            # updatable scenario
            if self.__check_rights_by_status(updated_contract.state) == "updatable":
                if "code" in contract:
                    raise ContractUpdateError("That fields are not editable in that permission!")
                return _output_result_success(
                    dict_representation=self.__update_contract_fields(
                        contract_input=contract,
                        updated_contract=updated_contract
                    )
                )
            # approvable scenario
            if self.__check_rights_by_status(updated_contract.state) == "approvable":
                # in “Negotiable” changes are possible only with the authority “Approve/ask for change”
                if not self.user.has_perms(ContractConfig.gql_mutation_approve_ask_for_change_contract_perms):
                    raise PermissionError("Unauthorized")
                return _output_result_success(
                    dict_representation=self.__update_contract_fields(
                        contract_input=contract,
                        updated_contract=updated_contract
                    )
                )
            if self.__check_rights_by_status(updated_contract.state) == "cannot_update":
                raise ContractUpdateError("In that state you cannot update!")
        except Exception as exc:
            return _output_exception(model_name="Contract", method="update", exception=exc)

    def __check_rights_by_status(self, status):
        state = "cannot_update"
        if status in [ContractModel.STATE_DRAFT, ContractModel.STATE_REQUEST_FOR_INFORMATION,
                      ContractModel.STATE_COUNTER]:
            state = "updatable"
        if status == ContractModel.STATE_NEGOTIABLE:
            state = "approvable"
        return state

    def __update_contract_fields(self, contract_input, updated_contract):
        # get the current policy_holder value
        current_policy_holder_id = updated_contract.policy_holder_id
        [setattr(updated_contract, key, contract_input[key]) for key in contract_input]
        # check if PH is set and not changed
        if current_policy_holder_id:
            if "policy_holder" in updated_contract.get_dirty_fields(check_relationship=True):
                raise ContractUpdateError("You cannot update already set PolicyHolder in Contract!")
        updated_contract.save(username=self.user.username)
        # save the communication
        historical_record = updated_contract.history.all().first()
        updated_contract.json_ext = _save_json_external(
            user_id=str(historical_record.user_updated.id),
            datetime=str(historical_record.date_updated),
            message="update contract status " + str(historical_record.state)
        )
        updated_contract.save(username=self.user.username)
        uuid_string = f"{updated_contract.id}"
        dict_representation = model_to_dict(updated_contract)
        dict_representation["id"], dict_representation["uuid"] = (str(uuid_string), str(uuid_string))
        return dict_representation

    @check_authentication
    def submit(self, contract):
        try:
            # check for submittion right perms/authorites
            if not self.user.has_perms(ContractConfig.gql_mutation_submit_contract_perms):
                raise PermissionError("Unauthorized")

            contract_id = f"{contract['id']}"
            contract_to_submit = ContractModel.objects.filter(id=contract_id).first()
            contract_details_list = {}
            contract_details_list["data"] = self.__gather_policy_holder_insuree(
                self.__validate_submission(contract_to_submit=contract_to_submit),
                contract_to_submit.amendment,
                contract_date_valid_from=None,
            )
            # contract valuation
            contract_contribution_plan_details = self.evaluate_contract_valuation(
                contract_details_result=contract_details_list,
            )
            contract_to_submit.amount_rectified = contract_contribution_plan_details["total_amount"]
            # send signal
            contract_to_submit.state = ContractModel.STATE_NEGOTIABLE
            signal_contract.send(sender=ContractModel, contract=contract_to_submit, user=self.user)
            dict_representation = model_to_dict(contract_to_submit)
            dict_representation["id"], dict_representation["uuid"] = (contract_id, contract_id)
            return _output_result_success(dict_representation=dict_representation)
        except Exception as exc:
            return _output_exception(model_name="Contract", method="submit", exception=exc)

    def __validate_submission(self, contract_to_submit):
        # check if we have a PolicyHoldes and any ContractDetails
        if not contract_to_submit.policy_holder:
            raise ContractUpdateError("The contract does not contain PolicyHolder!")
        contract_details = ContractDetailsModel.objects.filter(contract_id=contract_to_submit.id)
        if contract_details.count() == 0:
            raise ContractUpdateError("The contract does not contain any insuree!")
        # variable to check if we have right for submit
        state_right = self.__check_rights_by_status(contract_to_submit.state)
        # check if we can submit
        if state_right == "cannot_update":
            raise ContractUpdateError("The contract cannot be submitted because of current state!")
        if state_right == "approvable":
            raise ContractUpdateError("The contract has been already submitted!")
        return list(contract_details.values())

    def __gather_policy_holder_insuree(self, contract_details, amendment, contract_date_valid_from=None):
        result = []
        for cd in contract_details:
            ph_insuree = PolicyHolderInsuree.objects.filter(
                Q(insuree_id=cd['insuree_id'], last_policy__isnull=False)).first()
            policy_id = ph_insuree.last_policy.id if ph_insuree else None
            result.append({
                "id": f"{cd['id']}",
                "contribution_plan_bundle": f"{cd['contribution_plan_bundle_id']}",
                "policy_id": policy_id,
                "json_ext": cd['json_ext'],
                "contract_date_valid_from": contract_date_valid_from,
                "insuree_id": cd['insuree_id'],
                "amendment": amendment
            })
        return result

    @check_authentication
    def approve(self, contract):
        try:
            # check for approve/ask for change right perms/authorites
            if not self.user.has_perms(ContractConfig.gql_mutation_approve_ask_for_change_contract_perms):
                raise PermissionError("Unauthorized")
            contract_id = f"{contract['id']}"
            contract_to_approve = ContractModel.objects.filter(id=contract_id).first()
            # variable to check if we have right to approve
            state_right = self.__check_rights_by_status(contract_to_approve.state)
            # check if we can submit
            if state_right != "approvable":
                raise ContractUpdateError("You cannot approve this contract! The status of contract is not Negotiable!")
            contract_details_list = {}
            contract_details_list["data"] = self.__gather_policy_holder_insuree(
                list(ContractDetailsModel.objects.filter(contract_id=contract_to_approve.id).values()),
                contract_to_approve.amendment,
                contract_to_approve.date_valid_from,
            )
            # send signal - approve contract
            ccpd_service = ContractContributionPlanDetails(user=self.user)
            payment_service = PaymentService(user=self.user)
            signal_contract_approve.send(
                sender=ContractModel,
                contract=contract_to_approve,
                user=self.user,
                contract_details_list=contract_details_list,
                service_object=self,
                payment_service=payment_service,
                ccpd_service=ccpd_service
            )
            # ccpd.create_contribution(contract_contribution_plan_details)
            dict_representation = {}
            id_contract_approved = f"{contract_to_approve.id}"
            dict_representation["id"], dict_representation["uuid"] = id_contract_approved, id_contract_approved
            return _output_result_success(dict_representation=dict_representation)
        except Exception as exc:
            return _output_exception(model_name="Contract", method="approve", exception=exc)

    @check_authentication
    def counter(self, contract):
        try:
            # check for approve/ask for change right perms/authorites
            if not self.user.has_perms(ContractConfig.gql_mutation_approve_ask_for_change_contract_perms):
                raise PermissionError("Unauthorized")
            contract_id = f"{contract['id']}"
            contract_to_counter = ContractModel.objects.filter(id=contract_id).first()
            # variable to check if we have right to approve
            state_right = self.__check_rights_by_status(contract_to_counter.state)
            # check if we can submit
            if state_right != "approvable":
                raise ContractUpdateError("You cannot counter this contract! The status of contract is not Negotiable!")
            contract_to_counter.state = ContractModel.STATE_COUNTER
            signal_contract.send(sender=ContractModel, contract=contract_to_counter, user=self.user)
            dict_representation = model_to_dict(contract_to_counter)
            dict_representation["id"], dict_representation["uuid"] = (contract_id, contract_id)
            email = _send_email_notify_counter(
                code=contract_to_counter.code,
                name=contract_to_counter.policy_holder.trade_name,
                contact_name=contract_to_counter.policy_holder.contact_name,
                email=contract_to_counter.policy_holder.email,
            )
            return _output_result_success(dict_representation=dict_representation)
        except Exception as exc:
            return _output_exception(model_name="Contract", method="counter", exception=exc)

    @check_authentication
    def amend(self, contract):
        try:
            # check for amend right perms/authorites
            if not self.user.has_perms(ContractConfig.gql_mutation_amend_contract_perms):
                raise PermissionError("Unauthorized")
            contract_id = f"{contract['id']}"
            contract_to_amend = ContractModel.objects.filter(id=contract_id).first()
            # variable to check if we have right to amend contract
            state_right = self.__check_rights_by_status(contract_to_amend.state)
            # check if we can amend
            if state_right != "cannot_update" and contract_to_amend.state != ContractModel.STATE_TERMINATED:
                raise ContractUpdateError("You cannot amend this contract!")
            # create copy of the contract
            amended_contract = copy(contract_to_amend)
            amended_contract.id = None
            amended_contract.amendment += 1
            amended_contract.state = ContractModel.STATE_DRAFT
            contract_to_amend.state = ContractModel.STATE_ADDENDUM
            from core import datetime
            contract_to_amend.date_valid_to = datetime.datetime.now()
            # update contract - also copy contract details etc
            contract.pop("id")
            [setattr(amended_contract, key, contract[key]) for key in contract]
            # check if chosen fields are not edited
            if any(dirty_field in ["policy_holder", "code", "date_valid_from"] for dirty_field in
                   amended_contract.get_dirty_fields(check_relationship=True)):
                raise ContractUpdateError("You cannot update this field during amend contract!")
            signal_contract.send(sender=ContractModel, contract=contract_to_amend, user=self.user)
            signal_contract.send(sender=ContractModel, contract=amended_contract, user=self.user)
            # copy also contract details
            self.__copy_details(contract_id=contract_id, modified_contract=amended_contract)
            # evaluate amended contract amount notified
            contract_details_list = {}
            contract_details_list["data"] = self.__gather_policy_holder_insuree(
                list(ContractDetailsModel.objects.filter(contract_id=amended_contract.id).values()),
                contract_to_amend.amendment,
            )
            contract_contribution_plan_details = self.evaluate_contract_valuation(
                contract_details_result=contract_details_list,
                save=False
            )
            amended_contract.amount_notified = contract_contribution_plan_details["total_amount"]
            if "amount_notified" in amended_contract.get_dirty_fields():
                signal_contract.send(sender=ContractModel, contract=amended_contract, user=self.user)
            amended_contract_dict = model_to_dict(amended_contract)
            id_new_amended = f"{amended_contract.id}"
            amended_contract_dict["id"], amended_contract_dict["uuid"] = (id_new_amended, id_new_amended)
            return _output_result_success(dict_representation=amended_contract_dict)
        except Exception as exc:
            return _output_exception(model_name="Contract", method="amend", exception=exc)

    def __copy_details(self, contract_id, modified_contract):
        list_cd = list(ContractDetailsModel.objects.filter(contract_id=contract_id).all())
        for cd in list_cd:
            cd_new = copy(cd)
            cd_new.id = None
            cd_new.contract = modified_contract
            cd_new.save(username=self.user.username)

    @check_authentication
    def renew(self, contract):
        try:
            # check rights for renew contract
            if not self.user.has_perms(ContractConfig.gql_mutation_renew_contract_perms):
                raise PermissionError("Unauthorized")
            from core import datetime, datetimedelta
            contract_to_renew = ContractModel.objects.filter(id=contract["id"]).first()
            contract_id = contract["id"]
            # block renewing contract not in Updateable or Approvable state
            state_right = self.__check_rights_by_status(contract_to_renew.state)
            # check if we can renew
            if state_right != "cannot_update" and contract_to_renew.state != ContractModel.STATE_TERMINATED:
                raise ContractUpdateError("You cannot renew this contract!")
            # create copy of the contract - later we also copy contract detail
            renewed_contract = copy(contract_to_renew)
            # TO DO : if a policyholder is set, the contract details must be removed and PHinsuree imported again
            renewed_contract.id = None
            # Date to (the previous contract) became date From of the new contract (TBC if we need to add 1 day)
            # Date To of the new contract is calculated by DateFrom new contract + “Duration in month of previous contract“
            length_contract = (contract_to_renew.date_valid_to.year - contract_to_renew.date_valid_from.year) * 12 \
                              + (contract_to_renew.date_valid_to.month - contract_to_renew.date_valid_from.month)
            renewed_contract.date_valid_from = contract_to_renew.date_valid_to + datetimedelta(days=1)
            renewed_contract.date_valid_to = contract_to_renew.date_valid_to + datetimedelta(months=length_contract)
            renewed_contract.state, renewed_contract.version = (ContractModel.STATE_DRAFT, 1)
            renewed_contract.amount_rectified, renewed_contract.amount_due = (0, 0)
            renewed_contract.save(username=self.user.username)
            historical_record = renewed_contract.history.all().first()
            renewed_contract.json_ext = _save_json_external(
                user_id=str(historical_record.user_updated.id),
                datetime=str(historical_record.date_updated),
                message=f"contract renewed - state "
                        f"{historical_record.state}"
            )
            renewed_contract.save(username=self.user.username)
            # copy also contract details
            self.__copy_details(contract_id=contract_id, modified_contract=renewed_contract)
            renewed_contract_dict = model_to_dict(renewed_contract)
            id_new_renewed = f"{renewed_contract.id}"
            renewed_contract_dict["id"], renewed_contract_dict["uuid"] = (id_new_renewed, id_new_renewed)
            return _output_result_success(dict_representation=renewed_contract_dict)
        except Exception as exc:
            return _output_exception(model_name="Contract", method="renew", exception=exc)

    @check_authentication
    def delete(self, contract):
        try:
            # check rights for delete contract
            if not self.user.has_perms(ContractConfig.gql_mutation_delete_contract_perms):
                raise PermissionError("Unauthorized")
            contract_to_delete = ContractModel.objects.filter(id=contract["id"]).first()
            # block deleting contract not in Updateable or Approvable state
            if self.__check_rights_by_status(contract_to_delete.state) == "cannot_update":
                raise ContractUpdateError("Contract in that state cannot be deleted")
            contract_to_delete.delete(username=self.user.username)
            return {
                "success": True,
                "message": "Ok",
                "detail": "",
            }
        except Exception as exc:
            return _output_exception(model_name="Contract", method="delete", exception=exc)

    @check_authentication
    def terminate_contract(self):
        try:
            # TODO - add this service to the tasks.py in apscheduler once a day
            #  to check if contract might be terminated
            from core import datetime
            contracts_to_terminate = list(ContractModel.objects.filter(
                Q(date_valid_to__lt=datetime.datetime.now(), state=7)
            ))
            if len(contracts_to_terminate) > 0:
                for contract in contracts_to_terminate:
                    # we can marked that contract as a terminated
                    contract.state = ContractModel.STATE_TERMINATED
                    contract.save(username=self.user.username)
                    historical_record = contract.history.all().first()
                    contract.json_ext = _save_json_external(
                        user_id=str(historical_record.user_updated.id),
                        datetime=str(historical_record.date_updated),
                        message=f"contract terminated - state "
                                f"{historical_record.state}"
                    )
                    contract.save(username=self.user.username)
                return {
                    "success": True,
                    "message": "Ok",
                    "detail": "",
                }
            else:
                return {
                    "success": False,
                    "message": "No contracts to terminate!",
                    "detail": "We do not have any contract to be terminated!",
                }
        except Exception as exc:
            return _output_exception(model_name="Contract", method="terminateContract", exception=exc)

    @check_authentication
    def get_negative_amount_amendment(self, credit_note):
        try:
            if not self.user.has_perms(ContractConfig.gql_query_contract_perms):
                raise PermissionError("Unauthorized")

            contract_output_list = []
            payment_detail = PaymentDetail.get_queryset(PaymentDetail.objects.filter(
                payment__id=credit_note["id"]
            )).prefetch_related(
                'premium__contract_contribution_plan_details__contract_details__contract'
            ).prefetch_related(
                'premium__contract_contribution_plan_details'
            ).filter(premium__contract_contribution_plan_details__isnull=False)

            if len(list(payment_detail)) > 0:
                contribution_list_id = [pd.premium.id for pd in payment_detail]
                contract_list = ContractModel.objects.filter(
                    contractdetails__contractcontributionplandetails__contribution__id__in=contribution_list_id
                ).distinct()
                for contract in contract_list:
                    # look for approved contract (amendement)
                    if contract.state in [ContractModel.STATE_EFFECTIVE,
                                          ContractModel.STATE_EXECUTABLE] and contract.amendment > 0:
                        # get the contract which has the negative amount due
                        if contract.amount_due < 0:
                            contract_dict = model_to_dict(contract)
                            contract_id = f"{contract.id}"
                            contract_dict["id"], contract_dict["uuid"] = (contract_id, contract_id)
                            contract_output_list.append(contract_dict)
            # TODO not only get that contracts - but also do another things (it must be specified on wiki page)
            return _output_result_success(dict_representation=contract_output_list)
        except Exception as exc:
            return _output_exception(model_name="Contract", method="getNegativeAmountAmendment", exception=exc)


class ContractDetails(object):

    def __init__(self, user):
        self.user = user

    @check_authentication
    def update_from_ph_insuree(self, contract_details):
        try:
            contract_insuree_list = []
            policy_holder_insuree = PolicyHolderInsuree.objects.filter(
                policy_holder__id=contract_details['policy_holder_id'],
            )
            for phi in policy_holder_insuree:
                # TODO add the validity condition also!
                if phi.is_deleted is False and phi.contribution_plan_bundle:
                    cd = ContractDetailsModel(
                        **{
                            "contract_id": contract_details["contract_id"],
                            "insuree_id": phi.insuree.id,
                            "contribution_plan_bundle_id": f"{phi.contribution_plan_bundle.id}",
                            "json_ext": phi.json_ext,
                        }
                    )
                    # TODO add only the caclulation_rule section
                    cd.save(username=self.user.username)
                    uuid_string = f"{cd.id}"
                    dict_representation = model_to_dict(cd)
                    dict_representation["id"], dict_representation["uuid"] = (uuid_string, uuid_string)
                    dict_representation["policy_id"] = phi.last_policy.id if phi.last_policy else None
                    dict_representation["amendment"] = contract_details["amendment"]
                    dict_representation["contract_date_valid_from"] = cd.contract.date_valid_from
                    contract_insuree_list.append(dict_representation)
        except Exception as exc:
            return _output_exception(model_name="ContractDetails", method="updateFromPHInsuree", exception=exc)
        return _output_result_success(dict_representation=contract_insuree_list)

    @check_authentication
    def ph_insuree_to_contract_details(self, contract, ph_insuree):
        try:
            phi = PolicyHolderInsuree.objects.get(id=f'{ph_insuree["id"]}')
            # check for update contract right perms/authorites
            if not self.user.has_perms(ContractConfig.gql_mutation_update_contract_perms):
                raise PermissionError("Unauthorized")
            if phi.is_deleted is False and phi.contribution_plan_bundle:
                updated_contract = ContractModel.objects.get(id=f'{contract["id"]}')
                if updated_contract.state not in [ContractModel.STATE_DRAFT,
                                                  ContractModel.STATE_REQUEST_FOR_INFORMATION,
                                                  ContractModel.STATE_COUNTER]:
                    raise ContractUpdateError(
                        "You cannot update contract by adding insuree - contract not in updatable state!"
                    )
                if updated_contract.policy_holder is None:
                    raise ContractUpdateError(
                        "There is no policy holder in contract!"
                    )
                cd = ContractDetailsModel(
                    **{
                        "contract_id": contract["id"],
                        "insuree_id": phi.insuree.id,
                        "contribution_plan_bundle_id": f"{phi.contribution_plan_bundle.id}",
                    }
                )
                cd.save(username=self.user.username)
                uuid_string = f"{cd.id}"
                dict_representation = model_to_dict(cd)
                dict_representation["id"], dict_representation["uuid"] = (uuid_string, uuid_string)
                return _output_result_success(dict_representation=dict_representation)
            else:
                raise ContractUpdateError("You cannot insuree - is deleted or not enough data to create contract!")
        except Exception as exc:
            return _output_exception(model_name="ContractDetails", method="PHInsureToCDetatils", exception=exc)


class ContractContributionPlanDetails(object):

    def __init__(self, user):
        self.user = user

    @check_authentication
    def create_ccpd(self, ccpd, insuree_id):
        """"
            method to create contract contribution plan details
        """
        # get the relevant policy from the related product of contribution plan
        # policy objects get all related to this product
        insuree = Insuree.objects.filter(id=insuree_id).first()
        policies = self.__get_policy(
            insuree=insuree,
            date_valid_from=ccpd.date_valid_from,
            date_valid_to=ccpd.date_valid_to,
            product=ccpd.contribution_plan.benefit_plan,
        )
        return self.__create_contribution_from_policy(ccpd, policies)

    def __create_contribution_from_policy(self, ccpd, policies):
        if len(policies) == 1:
            ccpd.policy = policies[0]
            ccpd.save(username=self.user.username)
            return [ccpd]
        else:
            # create second ccpd because another policy was created - copy object and save
            ccpd_new = copy(ccpd)
            ccpd_new.date_valid_from = ccpd.date_valid_from
            ccpd_new.date_valid_to = policies[0].expiry_date
            ccpd_new.policy = policies[0]
            ccpd.date_valid_from = policies[0].expiry_date
            ccpd.date_valid_to = ccpd.date_valid_to
            ccpd.policy = policies[1]
            ccpd_new.save(username=self.user.username)
            ccpd.save(username=self.user.username)
            return [ccpd_new, ccpd]

    def __get_policy(self, insuree, date_valid_from, date_valid_to, product):
        from core import datetime
        policy_output = []
        # get all policies related to the product and insuree
        policies = Policy.objects.filter(product=product) \
            .filter(family__head_insuree=insuree) \
            .filter(start_date__lte=date_valid_to, expiry_date__gte=date_valid_from)
        # get covered policy, use count to run a COUNT query
        if policies.count() > 0:
            policies_covered = list(policies.order_by('start_date'))
        else:
            policies_covered = []
        missing_coverage = []
        # make sure the policies covers the contract : 
        last_date_covered = date_valid_from
        # get the start date of the new contract by updating last_date_covered to the policy.stop_date
        while last_date_covered < date_valid_to and len(policies_covered) > 0:
            cur_policy = policies_covered.pop()
            # to check if it does take the first
            if cur_policy.start_date <= last_date_covered:
                # Really unlikely we might create a policy that stop at curPolicy.startDate
                # (start at curPolicy.startDate - product length) and add it to policy_output
                last_date_covered = cur_policy.expiry_date
                policy_output.append(cur_policy)
            elif cur_policy.expiry_date <= date_valid_to:
                missing_coverage.append({'start': cur_policy.start_date, 'stop': last_date_covered})
                last_date_covered = cur_policy.expiry_date
                policy_output.append(cur_policy)

        for data in missing_coverage:
            policy_created, last_date_covered = self.create_contract_details_policies(insuree, product, data['start'],
                                                                                      data['stop'])
            if policy_created is not None and len(policy_created) > 0:
                policy_output += policy_created

        # now we create new policy
        while last_date_covered < date_valid_to:
            policy_created, last_date_covered = self.create_contract_details_policies(insuree, product,
                                                                                      last_date_covered, date_valid_to)
            if policy_created is not None and len(policy_created) > 0:
                policy_output += policy_created
        return policy_output

    def create_contract_details_policies(self, insuree, product, last_date_covered, date_valid_to):
        # create policy for insuree familly
        # TODO Policy with status - new open=32 in policy-be_py module
        policy_output = []
        while last_date_covered < date_valid_to:
            expiry_date = last_date_covered + relativedelta(months=product.insurance_period)
            cur_policy = Policy.objects.create(
                **{
                    "family": insuree.family,
                    "product": product,
                    "status": Policy.STATUS_ACTIVE,
                    "stage": Policy.STAGE_NEW,
                    "enroll_date": last_date_covered,
                    "start_date": last_date_covered,
                    "validity_from": last_date_covered,
                    "effective_date": last_date_covered,
                    "expiry_date": expiry_date,
                    "validity_to": None,
                    "audit_user_id": -1,
                }
            )
            last_date_covered = expiry_date
            policy_output.append(cur_policy)
        return policy_output, last_date_covered

    @check_authentication
    def contract_valuation(self, contract_contribution_plan_details):
        try:
            dict_representation = {}
            ccpd_list = []
            total_amount = 0
            amendment = 0
            for contract_details in contract_contribution_plan_details["contract_details"]:
                cpbd_list = ContributionPlanBundleDetails.objects.filter(
                    contribution_plan_bundle__id=str(contract_details["contribution_plan_bundle"])
                )
                amendment = contract_details["amendment"]
                for cpbd in cpbd_list:
                    ccpd = ContractContributionPlanDetailsModel(
                        **{
                            "contract_details_id": contract_details["id"],
                            "contribution_plan_id": f"{cpbd.contribution_plan.id}",
                            "policy_id": contract_details["policy_id"],
                        }
                    )
                    # rc - result of calculation
                    calculated_amount = 0
                    rc = run_calculation_rules(ccpd, "create", self.user)
                    if rc:
                        calculated_amount = rc[0][1] if rc[0][1] not in [None, False] else 0
                        total_amount += calculated_amount
                    ccpd_record = model_to_dict(ccpd)
                    ccpd_record["calculated_amount"] = calculated_amount
                    if contract_contribution_plan_details["save"]:
                        ccpd_list, total_amount, ccpd_record = self.__append_contract_cpd_to_list(
                            ccpd=ccpd,
                            cp=cpbd.contribution_plan,
                            date_valid_from=contract_details["contract_date_valid_from"],
                            insuree_id=contract_details["insuree_id"],
                            total_amount=total_amount,
                            calculated_amount=calculated_amount,
                            ccpd_list=ccpd_list,
                            ccpd_record=ccpd_record
                        )
                    if "id" not in ccpd_record:
                        ccpd_list.append(ccpd_record)
            if amendment > 0:
                # get the payment from the previous version of the contract
                contract_detail_id = contract_contribution_plan_details["contract_details"][0]["id"]
                cd = ContractDetailsModel.objects.get(id=contract_detail_id)
                contract_previous = ContractModel.objects.filter(
                    Q(amendment=amendment - 1, code=cd.contract.code)
                ).first()
                premium = ContractContributionPlanDetailsModel.objects.filter(
                    contract_details__contract__id=f'{contract_previous.id}'
                ).first().contribution
                payment_detail_contribution = PaymentDetail.objects.filter(premium=premium).first()
                payment_id = payment_detail_contribution.payment.id
                payment_object = Payment.objects.get(id=payment_id)
                received_amount = payment_object.received_amount if payment_object.received_amount else 0
                total_amount = float(total_amount) - float(received_amount)
            dict_representation['total_amount'] = total_amount
            dict_representation['contribution_plan_details'] = ccpd_list
            return _output_result_success(dict_representation=dict_representation)
        except Exception as exc:
            return _output_exception(
                model_name="ContractContributionPlanDetails",
                method="contractValuation",
                exception=exc
            )

    def __append_contract_cpd_to_list(self, ccpd, cp, date_valid_from, insuree_id, total_amount,
                                      calculated_amount, ccpd_list, ccpd_record):
        """helper private function to gather results to the list
           ccpd - contract contribution plan details
           cp - contribution plan
           return ccpd list and total amount
        """
        from core import datetime, datetimedelta
        # TODO - catch grace period from calculation rule if is defined
        #  grace_period = cp.calculation_rule etc
        #  length = cp.get_contribution_length(grace_period)
        length = cp.get_contribution_length()
        ccpd.date_valid_from = date_valid_from
        ccpd.date_valid_to = date_valid_from + datetimedelta(months=length)
        # TODO: calculate the number of CCPD to create in order to cover the contract lenght
        ccpd_results = self.create_ccpd(ccpd, insuree_id)
        ccpd_record = model_to_dict(ccpd)
        ccpd_record["calculated_amount"] = calculated_amount
        # TODO: support more that 2 CCPD
        # case 1 - single contribution
        if len(ccpd_results) == 1:
            uuid_string = f"{ccpd_results[0].id}"
            ccpd_record['id'], ccpd_record['uuid'] = (uuid_string, uuid_string)
            ccpd_list.append(ccpd_record)
        # case 2 - 2 contributions with 2 policies
        else:
            # there is additional contribution - we have to calculate/recalculate
            total_amount = total_amount - calculated_amount
            for ccpd_result in ccpd_results:
                length_ccpd = float((ccpd_result.date_valid_to.year - ccpd_result.date_valid_from.year) * 12 \
                                    + (ccpd_result.date_valid_to.month - ccpd_result.date_valid_from.month))
                periodicity = float(ccpd_result.contribution_plan.periodicity)
                # time part of splited as a fraction to count contribution value for that splited period properly
                part_time_period = length_ccpd / periodicity
                # rc - result calculation
                rc = run_calculation_rules(ccpd, "update", self.user)
                if rc:
                    calculated_amount = rc[0][1] * part_time_period if rc[0][1] not in [None, False] else 0
                    total_amount += calculated_amount
                ccpd_record = model_to_dict(ccpd_result)
                ccpd_record["calculated_amount"] = calculated_amount
                uuid_string = f"{ccpd_result.id}"
                ccpd_record['id'], ccpd_record['uuid'] = (uuid_string, uuid_string)
                ccpd_list.append(ccpd_record)
        return ccpd_list, total_amount, ccpd_record

    @check_authentication
    def create_contribution(self, contract_contribution_plan_details):
        try:
            dict_representation = {}
            contribution_list = []
            from core import datetime
            now = datetime.datetime.now()
            for ccpd in contract_contribution_plan_details["contribution_plan_details"]:
                contract_details = ContractDetailsModel.objects.get(id=f"{ccpd['contract_details']}")
                # create the contributions based on the ContractContributionPlanDetails
                if ccpd["contribution"] is None:
                    contribution = Premium.objects.create(
                        **{
                            "policy_id": ccpd["policy"],
                            "amount": ccpd["calculated_amount"],
                            "audit_user_id": -1,
                            "pay_date": now,
                            # TODO Temporary value pay_type - I have to get to know about this field what should be here
                            #  also ask about audit_user_id and pay_date value
                            "pay_type": " ",
                        }
                    )
                    ccpd_object = ContractContributionPlanDetailsModel.objects.get(id=ccpd["id"])
                    ccpd_object.contribution = contribution
                    ccpd_object.save(username=self.user.username)
                    contribution_record = model_to_dict(contribution)
                    contribution_list.append(contribution_record)
                    dict_representation["contributions"] = contribution_list
            return _output_result_success(dict_representation=dict_representation)
        except Exception as exc:
            return _output_exception(
                model_name="ContractContributionPlanDetails",
                method="createContribution",
                exception=exc
            )


class PaymentService(object):

    def __init__(self, user):
        self.user = user

    @check_authentication
    def create(self, payment, payment_details=None):
        try:
            dict_representation = {}
            payment_list = []
            from core import datetime
            now = datetime.datetime.now()
            p = update_or_create_payment(data=payment, user=self.user)
            dict_representation = model_to_dict(p)
            dict_representation['id'], dict_representation['uuid'] = (p.id, p.uuid)
            if payment_details:
                for payment_detail in payment_details:
                    pd = PaymentDetail.objects.create(
                        payment=Payment.objects.get(id=p.id),
                        audit_user_id=-1,
                        validity_from=now,
                        product_code=payment_detail["product_code"],
                        insurance_number=payment_detail["insurance_number"],
                        expected_amount=payment_detail["expected_amount"],
                        premium=payment_detail["premium"]
                    )
                    pd_record = model_to_dict(pd)
                    pd_record['id'] = pd.id
                    payment_list.append(pd_record)
            dict_representation["payment_details"] = payment_list
            return _output_result_success(dict_representation=dict_representation)
        except Exception as exc:
            return _output_exception(
                model_name="Payment",
                method="createPayment",
                exception=exc
            )

    @check_authentication
    def collect_payment_details(self, contract_contribution_plan_details):
        payment_details_data = []
        for ccpd in contract_contribution_plan_details:
            product_code = ContributionPlan.objects.get(id=ccpd["contribution_plan"]).benefit_plan.code
            insurance_number = ContractDetailsModel.objects.get(id=ccpd["contract_details"]).insuree.chf_id
            contribution = ContractContributionPlanDetailsModel.objects.get(id=ccpd["id"]).contribution
            expected_amount = ccpd["calculated_amount"]
            payment_details_data.append({
                "product_code": product_code,
                "insurance_number": insurance_number,
                "expected_amount": expected_amount,
                "premium": contribution
            })
        return payment_details_data


class ContractToInvoiceService(object):

    def __init__(self, user):
        self.user = user

    @classmethod
    @register_service_signal('create_invoice_from_contract')
    def create_invoice(self, instance, convert_to="Invoice", **kwargs):
        """ run convert the ContractContributionPlanDetails of the contract to invoice lines"""
        pass


def _output_exception(model_name, method, exception):
    return {
        "success": False,
        "message": f"Failed to {method} {model_name}",
        "detail": f"{exception}",
        "data": "",
    }


def _output_result_success(dict_representation):
    return {
        "success": True,
        "message": "Ok",
        "detail": "",
        "data": json.loads(json.dumps(dict_representation, cls=DjangoJSONEncoder)),
    }


def _save_json_external(user_id, datetime, message):
    return {
        "comments": [{
            "From": "Portal/webapp",
            "user": user_id,
            "date": datetime,
            "msg": message
        }]
    }


def _send_email_notify_counter(code, name, contact_name, email):
    try:
        email_to_send = send_mail(
            subject='Contract counter notification',
            message=get_message_counter_contract(
                language=settings.LANGUAGE_CODE.split('-')[0],
                code=code,
                name=name,
                contact_name=contact_name,
            ),
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False,
        )
        return email_to_send
    except BadHeaderError:
        return ValueError('Invalid header found.')


def check_unique_code(code):
    if ContractModel.objects.filter(code=code, is_deleted=False).exists():
        return [{"message": "Contract code %s already exists" % code}]
    return []
