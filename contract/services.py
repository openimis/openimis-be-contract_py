import json

from copy import copy

from django.db.models.query import QuerySet, Q
from django.contrib.auth.models import AnonymousUser
from django.core.serializers.json import DjangoJSONEncoder
from django.forms.models import model_to_dict

from contract.apps import ContractConfig
from contract.signals import signal_contract, signal_contract_approve
from contract.models import Contract as ContractModel, \
    ContractDetails as ContractDetailsModel, \
    ContractContributionPlanDetails as ContractContributionPlanDetailsModel

from policyholder.models import PolicyHolderInsuree
from contribution.models import Premium, Payer
from contribution_plan.models import ContributionPlanBundleDetails, ContributionPlan
from contribution_plan.services import get_contribution_length

from policy.models import Policy
from payment.models import Payment, PaymentDetail
from payment.services import update_or_create_payment
from insuree.models import Insuree


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
                })
                total_amount = self.evaluate_contract_valuation(
                    contract_details_result=result_ph_insuree,
                )["total_amount"]
                c.amount_notified = total_amount
            historical_record = c.history.all().last()
            c.json_ext = json.dumps(_save_json_external(
                user_id=historical_record.user_updated.id,
                datetime=historical_record.date_updated,
                message=f"create contract status {historical_record.state}"
            ), cls=DjangoJSONEncoder)
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
                    raise ContractUpdateError("That fields are not editable in that permission")
                return _output_result_success(
                    dict_representation=self.__update_contract_fields(
                        contract_input=contract,
                        updated_contract=updated_contract
                    )
                )
            # approvable scenario
            if self.__check_rights_by_status(updated_contract) == "approvable":
                # in “Negotiable” changes are possible only with the authority “Approve/ask for change”
                if not self.user.has_perms(ContractConfig.gql_mutation_approve_ask_for_change_contract_perms):
                    raise PermissionError("Unauthorized")
                return _output_result_success(
                    dict_representation=self.__update_contract_fields(
                        contract_input=contract,
                        updated_contract=updated_contract
                    )
                )
            if self.__check_rights_by_status(updated_contract) == "cannot_update":
                raise ContractUpdateError("In that state you cannot update")
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
        #check if PH is set and not changed
        if current_policy_holder_id:
            if "policy_holder" in updated_contract.get_dirty_fields(check_relationship=True):
                raise ContractUpdateError("You cannot update already set PolicyHolder in Contract")
        updated_contract.save(username=self.user.username)
        # save the communication
        historical_record = updated_contract.history.all().first()
        updated_contract.json_ext = json.dumps(_save_json_external(
            user_id=historical_record.user_updated.id,
            datetime=historical_record.date_updated,
            message="update contract status " + str(historical_record.state)
        ), cls=DjangoJSONEncoder)
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
                self.__validate_submission(contract_to_submit=contract_to_submit)
            )
            # contract valuation
            contract_contribution_plan_details = self.evaluate_contract_valuation(
                contract_details_result=contract_details_list,
            )
            contract_to_submit.amount_rectified = contract_contribution_plan_details["total_amount"]
            # create contract contribution based on service
            # TODO moved this create contribution to the approving contract
            #ccpd = ContractContributionPlanDetails(user=self.user)
            #ccpd.create_contribution(contract_contribution_plan_details)
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
            raise ContractUpdateError("The contract does not contain PolicyHolder")
        contract_details = ContractDetailsModel.objects.filter(contract_id=contract_to_submit.id)
        if contract_details.count() == 0:
            raise ContractUpdateError("The contract does not contain any insuree")
        # variable to check if we have right for submit
        state_right = self.__check_rights_by_status(contract_to_submit.state)
        # check if we can submit
        if state_right == "cannot_update":
            raise ContractUpdateError("The contract cannot be submitted because of current state")
        if state_right == "approvable":
            raise ContractUpdateError("The contract has been already submitted")
        return list(contract_details.values())

    def __gather_policy_holder_insuree(self, contract_details, contract_date_valid_from=None):
        return [
            {
                "id": f"{cd['id']}",
                "contribution_plan_bundle": f"{cd['contribution_plan_bundle_id']}",
                "policy_id": PolicyHolderInsuree.objects.filter(insuree_id=cd['insuree_id']).first().last_policy.id,
                "contract_date_valid_from": contract_date_valid_from,
                "insuree_id": cd['insuree_id']
            }
            for cd in contract_details
        ]

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
            if state_right is not "approvable":
                raise ContractUpdateError("You cannot approve this contract! The status of contract is not Negotiable")
            contract_details_list = {}
            contract_details_list["data"] = self.__gather_policy_holder_insuree(
                list(ContractDetailsModel.objects.filter(contract_id=contract_to_approve.id).values()),
                contract_to_approve.date_valid_from
            )
            # send signal - approve contract
            ccpd_service = ContractContributionPlanDetails(user=self.user)
            payment_service = PaymentService(user=self.user)
            contract_approved = signal_contract_approve.send(
                sender=ContractModel,
                contract=contract_to_approve,
                user=self.user,
                contract_details_list=contract_details_list,
                service_object=self,
                payment_service=payment_service,
                ccpd_service=ccpd_service
            )
            # ccpd.create_contribution(contract_contribution_plan_details)
            dict_representation = model_to_dict(contract_approved[0][1])
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
            if state_right is not "approvable":
                raise ContractUpdateError("You cannot counter this contract! The status of contract is not Negotiable")
            contract_to_counter.state = ContractModel.STATE_COUNTER
            signal_contract.send(sender=ContractModel, contract=contract_to_counter, user=self.user)
            dict_representation = model_to_dict(contract_to_counter)
            dict_representation["id"], dict_representation["uuid"] = (contract_id, contract_id)
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
            if state_right is not "cannot_update" and contract_to_amend.state is not ContractModel.STATE_TERMINATED:
                raise ContractUpdateError("You cannot amend this contract")
            # create copy of the contract
            amended_contract = copy(contract_to_amend)
            amended_contract.id = None
            amended_contract.amendment += 1
            amended_contract.state = ContractModel.STATE_DRAFT
            amended_contract.payment_reference = None
            contract_to_amend.state = ContractModel.STATE_ADDENDUM
            from core import datetime
            contract_to_amend.date_valid_to = datetime.datetime.now()
            # update contract - also copy contract details etc
            contract.pop("id")
            [setattr(amended_contract, key, contract[key]) for key in contract]
            # check if chosen fields are not edited
            if any(dirty_field in ["policy_holder", "code", "date_valid_from"] for dirty_field in amended_contract.get_dirty_fields(check_relationship=True)):
                raise ContractUpdateError("You cannot update this field during amend contract!")
            signal_contract.send(sender=ContractModel, contract=contract_to_amend, user=self.user)
            signal_contract.send(sender=ContractModel, contract=amended_contract, user=self.user)
            # copy also contract details and contract contribution plan details
            self.__copy_details(contract_id=contract_id, amended_contract=amended_contract)
            # evaluate amended contract amount notified
            contract_details_list = {}
            contract_details_list["data"] = self.__gather_policy_holder_insuree(
                list(ContractDetailsModel.objects.filter(contract_id=amended_contract.id).values())
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

    def __copy_details(self, contract_id, amended_contract):
        list_cd = ContractDetailsModel.objects.filter(contract_id=contract_id).all()
        for cd in list_cd:
            ccpd = ContractContributionPlanDetailsModel.objects.get(contract_details__id=f"{cd.id}")
            cd_new = copy(cd)
            cd_new.id = None
            cd_new.contract = amended_contract
            cd_new.json_ext = None
            cd_new.save(username=self.user.username)

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
                if phi.is_deleted == False and phi.contribution_plan_bundle:
                    cd = ContractDetailsModel(
                        **{
                            "contract_id": contract_details["contract_id"],
                            "insuree_id": phi.insuree.id,
                            "contribution_plan_bundle_id": f"{phi.contribution_plan_bundle.id}",
                        }
                    )
                    cd.save(self.user)
                    uuid_string = f"{cd.id}"
                    dict_representation = model_to_dict(cd)
                    dict_representation["id"], dict_representation["uuid"] = (uuid_string, uuid_string)
                    dict_representation["policy_id"] = phi.last_policy.id
                    contract_insuree_list.append(dict_representation)
        except Exception as exc:
            return _output_exception(model_name="ContractDetails", method="updateFromPHInsuree", exception=exc)
        return _output_result_success(dict_representation=contract_insuree_list)


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
            product_id=ccpd.contribution_plan.benefit_plan.id,
            insurance_period=ccpd.contribution_plan.benefit_plan.insurance_period
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

    def __get_policy(self, insuree, date_valid_from, date_valid_to, product_id, insurance_period):
        from core import datetime, datetimedelta
        policy_output = []
        # get all policies related to the product
        policies = Policy.objects.filter(product__id=product_id)
        # get covered policy
        policies_covered = policies.filter(
            Q(start_date__lte=date_valid_from, expiry_date__gte=date_valid_to)
        )

        if policies_covered.count() > 0:
            policy_output.append(policies_covered.first())
            return policy_output

        # look for partially policies - 1st case
        policies_partially_covered = policies.filter(
            Q(start_date__gt=date_valid_from, expiry_date__gte=date_valid_to) | Q(start_date__gt=date_valid_from, expiry_date=None),
            ~Q(start_date__gt=date_valid_to)
        )
        if policies_partially_covered.count() > 0:
            policy_retrieved = policies_partially_covered.first()
            policy = Policy.objects.create(
                **{
                    "family": insuree.family,
                    "product_id": product_id,
                    "status": Policy.STATUS_ACTIVE,
                    "stage": Policy.STAGE_NEW,
                    "enroll_date": date_valid_from,
                    "start_date": date_valid_from,
                    "validity_from": date_valid_from,
                    "effective_date": date_valid_from,
                    "expiry_date": policy_retrieved.start_date,
                    "validity_to": None,
                    "audit_user_id": -1,
                }
            )
            policy_output.append(policy)
            policy_output.append(policy_retrieved)
            return policy_output

        # look for partially policies - 2nd case
        policies_partially_covered = policies.filter(
            Q(start_date__lte=date_valid_from, expiry_date__lt=date_valid_to) | Q(start_date__lte=date_valid_from, expiry_date=None),
            ~Q(expiry_date__lt=date_valid_from)
        )
        if policies_partially_covered.count() > 0:
            policy_retrieved = policies_partially_covered.first()
            policy_output.append(policy_retrieved)
            policy = Policy.objects.create(
                **{
                    "family": insuree.family,
                    "product_id": product_id,
                    "status": Policy.STATUS_ACTIVE,
                    "stage": Policy.STAGE_NEW,
                    "enroll_date": policy_retrieved.expiry_date,
                    "start_date": policy_retrieved.expiry_date,
                    "validity_from": policy_retrieved.expiry_date,
                    "effective_date": policy_retrieved.expiry_date,
                    "expiry_date": date_valid_to,
                    "validity_to": None,
                    "audit_user_id": -1,
                }
            )
            policy_output.append(policy)
            return policy_output

        # else if we have no results
        # TODO Policy with status - new open=32 in policy-be_py module
        if len(policy_output) == 0:
            policy = Policy.objects.create(
                **{
                    "family": insuree.family,
                    "product_id": product_id,
                    "status": Policy.STATUS_ACTIVE,
                    "stage": Policy.STAGE_NEW,
                    "enroll_date": date_valid_from,
                    "start_date": date_valid_from,
                    "validity_from": date_valid_from,
                    "effective_date": date_valid_from,
                    "expiry_date": date_valid_from + datetimedelta(months=insurance_period),
                    "validity_to": None,
                    "audit_user_id": -1,
                }
            )
            policy_output.append(policy)
            return policy_output

    @check_authentication
    def contract_valuation(self, contract_contribution_plan_details):
        try:
            dict_representation = {}
            ccpd_list = []
            total_amount = 0
            for contract_details in contract_contribution_plan_details["contract_details"]:
                cpbd = ContributionPlanBundleDetails.objects.filter(
                    contribution_plan_bundle__id=str(contract_details["contribution_plan_bundle"])
                )[0]
                ccpd = ContractContributionPlanDetailsModel(
                    **{
                        "contract_details_id": contract_details["id"],
                        "contribution_plan_id": f"{cpbd.contribution_plan.id}",
                        "policy_id": contract_details["policy_id"],
                    }
                )
                # TODO here will be a function from calculation module
                #  to count the value for amount. And now temporary value is here
                #  until calculation module be developed
                calculated_amount = 250
                total_amount += calculated_amount
                ccpd_record = model_to_dict(ccpd)
                ccpd_record["calculated_amount"] = calculated_amount
                if contract_contribution_plan_details["save"]:
                    from core import datetime, datetimedelta
                    length = get_contribution_length(cpbd.contribution_plan)
                    ccpd.date_valid_from = contract_details["contract_date_valid_from"]
                    ccpd.date_valid_to = contract_details["contract_date_valid_from"] + datetimedelta(months=length)
                    ccpd_results = self.create_ccpd(ccpd, contract_details["insuree_id"])
                    ccpd_record = model_to_dict(ccpd)
                    ccpd_record["calculated_amount"] = calculated_amount
                    # case 1 - single contribution
                    if len(ccpd_results) == 1:
                        uuid_string = f"{ccpd_results[0].id}"
                        ccpd_record['id'], ccpd_record['uuid'] = (uuid_string, uuid_string)
                        ccpd_list.append(ccpd_record)
                    # case 2 - 2 contributions with 2 policies
                    else:
                        # there is additional contribution - we have to calculate/recalculate
                        # recalculate
                        total_amount = total_amount - calculated_amount
                        for ccpd_result in ccpd_results:
                            # TODO here will be a function from calculation module
                            #  to count the value for amount. And now temporary value is here
                            #  until calculation module be developed
                            calculated_amount = 250
                            total_amount += calculated_amount
                            ccpd_record = model_to_dict(ccpd_result)
                            ccpd_record["calculated_amount"] = calculated_amount
                            ccpd_record['id'], ccpd_record['uuid'] = (ccpd_result.id, ccpd_result.id)
                            ccpd_list.append(ccpd_record)
                if "id" not in ccpd_record:
                    ccpd_list.append(ccpd_record)
            dict_representation['total_amount'] = total_amount
            dict_representation['contribution_plan_details'] = ccpd_list
            return _output_result_success(dict_representation=dict_representation)
        except Exception as exc:
            return _output_exception(
                model_name="ContractContributionPlanDetails",
                method="contractValuation",
                exception=exc
            )

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
                        expected_amount=payment_detail["expected_amount"]
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
            expected_amount = ccpd["calculated_amount"]
            payment_details_data.append({
                "product_code": product_code,
                "insurance_number": insurance_number,
                "expected_amount": expected_amount
            })
        return payment_details_data

    def submit(self, payment):
        pass

    def update(self, payment):
        pass

    def delete(self, payment):
        pass

    def assign_credit_note(self, payment):
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