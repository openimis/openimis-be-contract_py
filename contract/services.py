import json
import logging
import traceback
import uuid
from copy import copy
from decimal import Decimal

from calculation.services import run_calculation_rules
from contribution.models import Premium
from core import datetime, datetimedelta
from core.signals import register_service_signal
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.core.mail import BadHeaderError, send_mail
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.query import Q
from django.db import transaction
from django.forms.models import model_to_dict
from django.utils.translation import gettext as _
from payment.models import Payment, PaymentDetail
from payment.services import update_or_create_payment
from policy.models import Policy
from policyholder.models import PolicyHolderInsuree, has_hybrid_phu_perms, PolicyHolder

from contract.apps import ContractConfig
from contract.models import Contract as ContractModel
from contract.models import (
    ContractContributionPlanDetails as ContractContributionPlanDetailsModel,
)
from contract.models import ContractDetails as ContractDetailsModel
from contract.signals import signal_contract, signal_contract_approve

from .config import get_message_counter_contract

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
            incoming_code = contract.get("code")
            if check_unique_code(incoming_code):
                raise ValidationError(
                    _("Contract code %s already exists" % incoming_code)
                )
            if not (self.user.has_perms(
                ContractConfig.gql_mutation_create_contract_perms)
                or has_hybrid_phu_perms(
                    self.user,
                    PolicyHolder.objects.filter(contract__id=contract['id']).first(),
                    ContractConfig.gql_mutation_create_contract_policyholder_portal_perms
                )
            ):
                raise PermissionError(_("Unauthorized"))
            if not contract.get("date_valid_to", None) or not contract.get(
                "date_valid_from", None
            ):
                raise Exception(_("contract.mandatory_fields.date_valid"))
            c = ContractModel(**contract)
            if c.date_valid_to < c.date_valid_from:
                raise Exception(_("contract.validation.date_valid"))
            c.state = ContractModel.STATE_DRAFT
            c.save(user=self.user)
            uuid_string = f"{c.id}"
            # check if the PH is set
            if c.policy_holder:
                # run services updateFromPHInsuree and Contract Valuation
                cd_service = ContractDetails(user=self.user)
                result_ph_insuree = cd_service.get_details_from_ph_insuree(contract=c)
                if result_ph_insuree["success"]:
                    result_contract_valuation = self.contract_valuation(
                        contract=c, contract_details_list=result_ph_insuree["data"]
                    )
                else:
                    return result_ph_insuree
                if (
                    not result_contract_valuation
                    or result_contract_valuation["success"] is False
                ):
                    logger.error(
                        _(
                            "contract valuation failed %s"
                            % str(result_contract_valuation)
                        )
                    )
                    raise Exception(
                        _(
                            "contract valuation failed %s"
                            % str(result_contract_valuation)
                        )
                    )
                c.amount_notified = result_contract_valuation["data"]["total_amount"]
            historical_record = c.history.all().last()
            c.json_ext = _save_json_external(
                user_id=str(historical_record.user_updated.id),
                datetime=str(historical_record.date_updated),
                message=_("create contract status %s" % historical_record.state),
            )
            c.save(user=self.user)
            dict_representation = model_to_dict(c)
            dict_representation["id"], dict_representation["uuid"] = (
                str(uuid_string),
                str(uuid_string),
            )
        except Exception as exc:
            return _output_exception(
                model_name="Contract", method="create", exception=exc
            )
        return _output_result_success(dict_representation=dict_representation)

    # TODO update contract scenario according to wiki page
    @check_authentication
    def update(self, contract):
        try:
            # check rights for contract / amendments
            if not (
                self.user.has_perms(
                    ContractConfig.gql_mutation_update_contract_perms 
                    + ContractConfig.gql_mutation_approve_ask_for_change_contract_perms
                )
                or has_hybrid_phu_perms(
                    self.user,
                    PolicyHolder.objects.filter(contract__id=contract['id']).first(),
                    ContractConfig.gql_mutation_update_contract_policyholder_portal_perms
                )
                
            ):
                raise PermissionError("Unauthorized")
            updated_contract = ContractModel.objects.filter(id=contract["id"]).first()
            # updatable scenario
            if self.__check_rights_by_status(updated_contract.state) == "updatable":
                if "code" in contract:
                    raise ContractUpdateError(
                        _("That fields are not editable in that permission!")
                    )
                return _output_result_success(
                    dict_representation=self.__update_contract_fields(
                        contract_input=contract, updated_contract=updated_contract
                    )
                )
            # approvable scenario
            if self.__check_rights_by_status(updated_contract.state) == "approvable":
                # in “Negotiable” changes are possible only with the authority “Approve/ask for change”
                if not self.user.has_perms(
                    ContractConfig.gql_mutation_approve_ask_for_change_contract_perms
                ):
                    raise PermissionError(_("unauthorized"))
                return _output_result_success(
                    dict_representation=self.__update_contract_fields(
                        contract_input=contract, updated_contract=updated_contract
                    )
                )
            if self.__check_rights_by_status(updated_contract.state) == "cannot_update":
                raise ContractUpdateError(_("contract.validation.locked_by_state"))
        except Exception as exc:
            return _output_exception(
                model_name="Contract", method="update", exception=exc
            )

    def __check_rights_by_status(self, status):
        state = "cannot_update"
        if status in [
            ContractModel.STATE_DRAFT,
            ContractModel.STATE_REQUEST_FOR_INFORMATION,
            ContractModel.STATE_COUNTER,
        ]:
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
            if "policy_holder" in updated_contract.get_dirty_fields(
                check_relationship=True
            ):
                raise ContractUpdateError(
                    _("You cannot update already set PolicyHolder in Contract!")
                )
        updated_contract.save(user=self.user)
        # save the communication
        historical_record = updated_contract.history.all().first()
        updated_contract.json_ext = _save_json_external(
            user_id=str(historical_record.user_updated.id),
            datetime=str(historical_record.date_updated),
            message=_("update contract status %s" % str(historical_record.state)),
        )
        updated_contract.save(user=self.user)
        uuid_string = f"{updated_contract.id}"
        dict_representation = model_to_dict(updated_contract)
        dict_representation["id"], dict_representation["uuid"] = (
            str(uuid_string),
            str(uuid_string),
        )
        return dict_representation

    @check_authentication
    def submit(self, contract):
        try:
               # check for submittion right perms/authorites
            if not (self.user.has_perms(
                ContractConfig.gql_mutation_submit_contract_perms)
                or has_hybrid_phu_perms(
                    self.user,
                    PolicyHolder.objects.filter(contract__id=contract['id']).first(),
                    ContractConfig.gql_mutation_submit_contract_policyholder_portal_perms
                )
            ):
                raise PermissionError("Unauthorized")

            contract_id = f"{contract['id']}"
            contract_to_submit = ContractModel.objects.filter(id=contract_id).first()
            if not contract_to_submit:
                raise ContractUpdateError(
                    _("No contract found for this id %s" % contract["id"])
                )
            contract_to_submit = self.__validate_submission(contract_to_submit=contract_to_submit)

            # contract valuation
            valuation_result = self.contract_valuation(contract_to_submit)
            if valuation_result["success"]:
                contract_to_submit.amount_rectified = valuation_result["data"][
                    "total_amount"
                ]
            else:
                raise Exception(
                    _("Unable to valuate contract: %s" % valuation_result["message"])
                )
            # send signal
            contract_to_submit.state = ContractModel.STATE_NEGOTIABLE
            signal_contract.send(
                sender=ContractModel, contract=contract_to_submit, user=self.user
            )
            dict_representation = model_to_dict(contract_to_submit)
            dict_representation["id"], dict_representation["uuid"] = (
                contract_id,
                contract_id,
            )
            return _output_result_success(dict_representation=dict_representation)
        except Exception as exc:
            return _output_exception(
                model_name="Contract", method="submit", exception=exc
            )

    def __validate_submission(self, contract_to_submit):
        # check if we have a PolicyHoldes and any ContractDetails
        if not contract_to_submit.policy_holder:
            raise ContractUpdateError(_("The contract does not contain PolicyHolder!"))
        contract_details = ContractDetailsModel.objects.filter(
            contract=contract_to_submit, is_deleted=False
        )
        if contract_details.count() == 0:
            raise ContractUpdateError(_("contract.validation.no_details"))
        # variable to check if we have right for submit
        state_right = self.__check_rights_by_status(contract_to_submit.state)
        # check if we can submit
        if state_right == "cannot_update":
            raise ContractUpdateError(
                _("The contract cannot be submitted because of current state!")
            )
        if state_right == "approvable":
            raise ContractUpdateError(_("The contract has been already submitted!"))
        return contract_to_submit

    @check_authentication
    def approve(self, contract):
        try:
            # check for approve/ask for change right perms/authorites
            if not self.user.has_perms(
                ContractConfig.gql_mutation_approve_ask_for_change_contract_perms
            ):
                raise PermissionError(_("unauthorized"))
            contract_id = f"{contract['id']}"
            contract_to_approve = (
                ContractModel.objects.filter(id=contract_id, is_deleted=False)
                .order_by("-amendment")
                .first()
            )
            if not contract_to_approve:
                raise ContractUpdateError(
                    _("No contract found for this id %s" % contract["id"])
                )
            # variable to check if we have right to approve
            state_right = self.__check_rights_by_status(contract_to_approve.state)
            # check if we can submit
            if state_right != "approvable":
                raise ContractUpdateError(
                    _(
                        "You cannot approve this contract! The status of contract is not Negotiable!"
                    )
                )
            # send signal - approve contract
            ccpd_service = ContractContributionPlanDetails(user=self.user)
            payment_service = PaymentService(user=self.user)
            signal_contract_approve.send(
                sender=ContractModel,
                instance=contract_to_approve,
                user=self.user,
                service_object=self,
                payment_service=payment_service,
                ccpd_service=ccpd_service,
            )
            # ccpd.create_contribution(contract_contribution_plan_details)
            dict_representation = {}
            id_contract_approved = f"{contract_to_approve.id}"
            dict_representation["id"], dict_representation["uuid"] = (
                id_contract_approved,
                id_contract_approved,
            )
            return _output_result_success(dict_representation=dict_representation)
        except Exception as exc:
            return _output_exception(
                model_name="Contract", method="approve", exception=exc
            )

    @check_authentication
    def counter(self, contract):
        try:
            # check for approve/ask for change right perms/authorites
            if not self.user.has_perms(
                ContractConfig.gql_mutation_approve_ask_for_change_contract_perms
            ):
                raise PermissionError("Unauthorized")
            contract_id = f"{contract['id']}"
            contract_to_counter = ContractModel.objects.filter(id=contract_id).first()
            # variable to check if we have right to approve
            state_right = self.__check_rights_by_status(contract_to_counter.state)
            # check if we can submit
            if state_right != "approvable":
                raise ContractUpdateError(
                    _(
                        "You cannot counter this contract! The status of contract is not Negotiable!"
                    )
                )
            contract_to_counter.state = ContractModel.STATE_COUNTER
            signal_contract.send(
                sender=ContractModel, contract=contract_to_counter, user=self.user
            )
            dict_representation = model_to_dict(contract_to_counter)
            dict_representation["id"], dict_representation["uuid"] = (
                contract_id,
                contract_id,
            )
            _send_email_notify_counter(
                code=contract_to_counter.code,
                name=contract_to_counter.policy_holder.trade_name,
                contact_name=contract_to_counter.policy_holder.contact_name,
                email=contract_to_counter.policy_holder.email,
            )
            return _output_result_success(dict_representation=dict_representation)
        except Exception as exc:
            return _output_exception(
                model_name="Contract", method="counter", exception=exc
            )

    @check_authentication
    def amend(self, contract):
        try:
            # check for amend right perms/authorites
            if not (
                self.user.has_perms(ContractConfig.gql_mutation_amend_contract_perms)
                or has_hybrid_phu_perms(
                    self.user,
                    PolicyHolder.objects.filter(contract__id=contract['id']).first(),
                    ContractConfig.gql_mutation_amend_contract_policyholder_portal_perms
                )
            ):
                raise PermissionError("Unauthorized")
            contract_id = f"{contract['id']}"
            contract_to_amend = ContractModel.objects.filter(id=contract_id).first()
            # variable to check if we have right to amend contract
            state_right = self.__check_rights_by_status(contract_to_amend.state)
            # check if we can amend
            if (
                state_right != "cannot_update"
                and contract_to_amend.state != ContractModel.STATE_TERMINATED
            ):
                raise ContractUpdateError(_("You cannot amend this contract!"))
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
            if any(
                dirty_field in ["policy_holder", "code", "date_valid_from"]
                for dirty_field in amended_contract.get_dirty_fields(
                    check_relationship=True
                )
            ):
                raise ContractUpdateError(
                    _("You cannot update this field during amend contract!")
                )
            signal_contract.send(
                sender=ContractModel, contract=contract_to_amend, user=self.user
            )
            signal_contract.send(
                sender=ContractModel, contract=amended_contract, user=self.user
            )
            # copy also contract details
            self.__copy_details(
                contract_id=contract_id, modified_contract=amended_contract
            )
            # evaluate amended contract amount notified

            valuation_result = self.contract_valuation(amended_contract)
            amended_contract.amount_notified = valuation_result["data"]["total_amount"]
            if "amount_notified" in amended_contract.get_dirty_fields():
                signal_contract.send(
                    sender=ContractModel, contract=amended_contract, user=self.user
                )
            amended_contract_dict = model_to_dict(amended_contract)
            id_new_amended = f"{amended_contract.id}"
            amended_contract_dict["id"], amended_contract_dict["uuid"] = (
                id_new_amended,
                id_new_amended,
            )
            return _output_result_success(dict_representation=amended_contract_dict)
        except Exception as exc:
            return _output_exception(
                model_name="Contract", method="amend", exception=exc
            )

    def __copy_details(self, contract_id, modified_contract):
        list_cd = list(
            ContractDetailsModel.objects.filter(contract_id=contract_id).all()
        )
        for cd in list_cd:
            cd_new = copy(cd)
            cd_new.id = None
            cd_new.contract = modified_contract
            cd_new.save(userself.user)

    @check_authentication
    def renew(self, contract):
        try:
            # check rights for renew contract
            if not self.user.has_perms(
                ContractConfig.gql_mutation_renew_contract_perms
            ):
                raise PermissionError("Unauthorized")
            contract_to_renew = ContractModel.objects.filter(id=contract["id"]).first()
            contract_id = contract["id"]
            # block renewing contract not in Updateable or Approvable state
            state_right = self.__check_rights_by_status(contract_to_renew.state)
            # check if we can renew
            if (
                state_right != "cannot_update"
                and contract_to_renew.state != ContractModel.STATE_TERMINATED
            ):
                raise ContractUpdateError(_("You cannot renew this contract!"))
            # create copy of the contract - later we also copy contract detail
            renewed_contract = copy(contract_to_renew)
            # TO DO : if a policyholder is set, the contract details must be removed and PHinsuree imported again
            renewed_contract.id = None
            # Date to (the previous contract) became date From of the new contract (TBC if we need to add 1 day)
            # Date To of the new contract is calculated by DateFrom new contract
            # + “Duration in month of previous contract“
            length_contract = (
                contract_to_renew.date_valid_to.year
                - contract_to_renew.date_valid_from.year
            ) * 12 + (
                contract_to_renew.date_valid_to.month
                - contract_to_renew.date_valid_from.month
            )
            renewed_contract.date_valid_from = (
                contract_to_renew.date_valid_to + datetimedelta(days=1)
            )
            renewed_contract.date_valid_to = (
                contract_to_renew.date_valid_to + datetimedelta(months=length_contract)
            )
            renewed_contract.state, renewed_contract.version = (
                ContractModel.STATE_DRAFT,
                1,
            )
            renewed_contract.amount_rectified, renewed_contract.amount_due = (0, 0)
            renewed_contract.save(user=self.user)
            historical_record = renewed_contract.history.all().first()
            renewed_contract.json_ext = _save_json_external(
                user_id=str(historical_record.user_updated.id),
                datetime=str(historical_record.date_updated),
                message=f"contract renewed - state " f"{historical_record.state}",
            )
            renewed_contract.save(user=self.user)
            # copy also contract details
            self.__copy_details(
                contract_id=contract_id, modified_contract=renewed_contract
            )
            renewed_contract_dict = model_to_dict(renewed_contract)
            id_new_renewed = f"{renewed_contract.id}"
            renewed_contract_dict["id"], renewed_contract_dict["uuid"] = (
                id_new_renewed,
                id_new_renewed,
            )
            return _output_result_success(dict_representation=renewed_contract_dict)
        except Exception as exc:
            return _output_exception(
                model_name="Contract", method="renew", exception=exc
            )

    @check_authentication
    def delete(self, contract):
        try:
            # check rights for delete contract
            if not self.user.has_perms(
                ContractConfig.gql_mutation_delete_contract_perms
            ):
                raise PermissionError(_("unauthorized"))
            contract_to_delete = ContractModel.objects.filter(id=contract["id"]).first()
            # block deleting contract not in Updateable or Approvable state
            if (
                self.__check_rights_by_status(contract_to_delete.state)
                == "cannot_update"
            ):
                raise ContractUpdateError(_("Contract in that state cannot be deleted"))
            contract_to_delete.delete(user=self.user)
            return {
                "success": True,
                "message": "Ok",
                "detail": "",
            }
        except Exception as exc:
            return _output_exception(
                model_name="Contract", method="delete", exception=exc
            )

    @check_authentication
    def terminate_contract(self):
        try:
            # TODO - add this service to the tasks.py in apscheduler once a day
            #  to check if contract might be terminated
            from core import datetime

            contracts_to_terminate = list(
                ContractModel.objects.filter(
                    Q(date_valid_to__lt=datetime.datetime.now(), state=ContractModel.STATE_EFFECTIVE)
                )
            )
            if len(contracts_to_terminate) > 0:
                for contract in contracts_to_terminate:
                    # we can marked that contract as a terminated
                    contract.state = ContractModel.STATE_TERMINATED
                    contract.save(user=self.user)
                    historical_record = contract.history.all().first()
                    contract.json_ext = _save_json_external(
                        user_id=str(historical_record.user_updated.id),
                        datetime=str(historical_record.date_updated),
                        message=f"contract terminated - state "
                        f"{historical_record.state}",
                    )
                    contract.save(user=self.user)
                return {
                    "success": True,
                    "message": "Ok",
                    "detail": "",
                }
            else:
                return {
                    "success": False,
                    "message": _("No contracts to terminate!"),
                    "detail": _("We do not have any contract to be terminated!"),
                }
        except Exception as exc:
            return _output_exception(
                model_name="Contract", method="terminateContract", exception=exc
            )

    @check_authentication
    def get_negative_amount_amendment(self, credit_note):
        try:
            if not self.user.has_perms(ContractConfig.gql_query_contract_perms):
                raise PermissionError("Unauthorized")

            contract_output_list = []
            payment_detail = (
                PaymentDetail.get_queryset(
                    PaymentDetail.objects.filter(payment__id=credit_note["id"])
                )
                .prefetch_related(
                    "premium__contract_contribution_plan_details__contract_details__contract"
                )
                .prefetch_related("premium__contract_contribution_plan_details")
                .filter(premium__contract_contribution_plan_details__isnull=False)
            )

            if len(list(payment_detail)) > 0:
                contribution_list_id = [pd.premium.id for pd in payment_detail]
                contract_list = ContractModel.objects.filter(
                    contractdetails__contractcontributionplandetails__contribution__id__in=contribution_list_id
                ).distinct()
                for contract in contract_list:
                    # look for approved contract (amendement)
                    if (
                        contract.state
                        in [
                            ContractModel.STATE_EFFECTIVE,
                            ContractModel.STATE_EXECUTABLE,
                        ]
                        and contract.amendment > 0
                    ):
                        # get the contract which has the negative amount due
                        if contract.amount_due < 0:
                            contract_dict = model_to_dict(contract)
                            contract_id = f"{contract.id}"
                            contract_dict["id"], contract_dict["uuid"] = (
                                contract_id,
                                contract_id,
                            )
                            contract_output_list.append(contract_dict)
            # TODO not only get that contracts - but also do another things (it must be specified on wiki page)
            return _output_result_success(dict_representation=contract_output_list)
        except Exception as exc:
            return _output_exception(
                model_name="Contract",
                method="getNegativeAmountAmendment",
                exception=exc,
            )

    def contract_valuation(self, contract, contract_details_list=None, save=False):
        ccpd_service = ContractContributionPlanDetails(self.user)
        try:
            if contract_details_list is None:
                contract_details_list = contract.contractdetails_set.filter(is_deleted=False)
            dict_representation = {}
            total_amount = 0
            amendment = contract.amendment
            ccpd_record = []
            errors = []
            for contract_details in contract_details_list:
                cpbd_list = (
                    contract_details.contribution_plan_bundle
                    .contributionplanbundledetails_set.filter(
                        *contract.contract_business_validity(),
                        *contract.contract_business_validity(prefix='contribution_plan__'),
                        is_deleted=False
                    )
                )

                for cpbd in cpbd_list:
                    ccpd = ContractContributionPlanDetailsModel(
                        **{
                            "contract_details": contract_details,
                            "contribution_plan": cpbd.contribution_plan,
                            "date_valid_from": contract.date_valid_from,
                            "date_valid_to": contract.date_valid_to,
                        }
                    )
                    ccpd.amount = run_calculation_rules(ccpd, "value", self.user)
                    if ccpd.amount is False or ccpd.amount is None:
                        errors.append(
                            f"no amount calculated for {ccpd.contract_details.insuree}"
                            + f" - {ccpd.contribution_plan.code}"
                        )
                    # value from strategy
                    else:
                        total_amount += ccpd.amount
                        if save:
                            ccpd_record.extend(
                                ccpd_service.split(
                                    ccpd, contract_details.insuree
                                )
                            )
                        else:
                            ccpd_record.append(ccpd)
            if errors:
                raise Exception("failed to compute values:" + ',\n'.join(errors))
            if amendment > 0:
                # get the payment from the previous version of the contract
                contract_detail_id = contract_details_list[0].id
                cd = ContractDetailsModel.objects.get(id=contract_detail_id)
                contract_previous = ContractModel.objects.filter(
                    Q(amendment=amendment - 1, code=cd.contract.code)
                ).first()
                premium = (
                    ContractContributionPlanDetailsModel.objects.filter(
                        contract_details__contract__id=f"{contract_previous.id}"
                    )
                    .first()
                    .contribution
                )
                payment_detail_contribution = PaymentDetail.objects.filter(
                    premium=premium
                ).first()
                payment_id = payment_detail_contribution.payment.id
                payment_object = Payment.objects.get(id=payment_id)
                total_amount -= (
                    payment_object.received_amount
                    if payment_object.received_amount
                    else 0
                )
            dict_representation["total_amount"] = total_amount
            dict_representation["contribution_plan_details"] = ccpd_record
            return _output_result_success(dict_representation, object_list=True)
        except Exception as exc:
            return _output_exception(
                model_name="ContractContributionPlanDetails",
                method="contractValuation",
                exception=exc,
            )


class ContractDetails(object):
    def __init__(self, user):
        self.user = user

    # contract_details
    def get_details_from_ph_insuree(self, contract, ph_insuree=None):
        contract_insuree_list = []
        if not contract.policy_holder:
            _output_result_success(dict_representation=contract_insuree_list)
        try:
            policy_holder_insuree = PolicyHolderInsuree.objects.filter(
                *contract.contract_business_validity(),
                policy_holder=contract.policy_holder,
                is_deleted=False,
            )
            if ph_insuree and isinstance(ph_insuree, list):
                policy_holder_insuree = policy_holder_insuree.filter(
                    id__in=ph_insuree
                )

            for phi in policy_holder_insuree:
                # TODO add the validity condition also!
                if phi.contribution_plan_bundle:
                    cd = ContractDetailsModel(
                        **{
                            "contract_id": contract.id,
                            "insuree_id": phi.insuree.id,
                            "contribution_plan_bundle": phi.contribution_plan_bundle,
                            "json_ext": phi.json_ext,
                        }
                    )
                    cd.save(user=self.user)
                    contract_insuree_list.append(cd)
        except Exception as exc:
            return _output_exception(
                model_name="ContractDetails",
                method="updateFromPHInsuree",
                exception=exc,
            )
        return _output_result_success(contract_insuree_list, object_list=True)


class ContractContributionPlanDetails(object):

    def __init__(self, user):
        self.user = user

    @check_authentication
    def split(self, ccpd, insuree):
        """ "
        method to create contract contribution plan details
        """

        date_valid_from = ccpd.date_valid_from
        # get date from strategy
        validity_dates = run_calculation_rules(
            ccpd,
            "validity",
            self.user,
            validity_from=ccpd.contract_details.contract.date_valid_from,
            validity_to=ccpd.contract_details.contract.date_valid_to,
        )

        if (
            validity_dates
            and "effective_date" in validity_dates
            and validity_dates["effective_date"]
        ):
            date_valid_from = datetime.date.from_ad_date(
                validity_dates["effective_date"]
            )

        if (
            validity_dates
            and "expiry_date" in validity_dates
            and validity_dates["expiry_date"]
        ):
            date_valid_to = datetime.date.from_ad_date(validity_dates["expiry_date"])
        # get the relevant policy from the related product of contribution plan
        # policy objects get all related to this product
        policies = self.__get_policy(
            insuree=insuree,
            date_valid_from=date_valid_from,
            date_valid_to=date_valid_to,
            product=ccpd.contribution_plan.benefit_plan,
        )
        calculated_amount = ccpd.amount
        list_ccpd = []
        amount_booked = 0
        unit_amount = calculated_amount / (date_valid_to - date_valid_from).days
        i = 0
        for policy in policies:
            if i > 1:
                ccpd = ccpd.copy()
            i += 1
            ccpd.policy = policy
            ccpd.date_valid_from = max(
                datetime.datetime.fromordinal(policy.effective_date.toordinal()),
                date_valid_from,
            )
            ccpd.date_valid_to = min(
                datetime.datetime.fromordinal(policy.expiry_date.toordinal()),
                date_valid_to,
            )

            if len(policies) == i:
                ccpd.amount =  Decimal(str(calculated_amount)) - amount_booked
            else:
                from datetime import time
                if isinstance(date_valid_from, datetime.date) and not isinstance(date_valid_from, datetime.datetime):
                    ccpd.date_valid_from = datetime.datetime.combine(date_valid_from, time.min)
                if isinstance(date_valid_to, datetime.date) and not isinstance(date_valid_to, datetime.datetime):
                    ccpd.date_valid_to = datetime.datetime.combine(date_valid_to, time.min)
                ccpd.amount = round(
                    Decimal((ccpd.date_valid_to - ccpd.date_valid_from).days) * Decimal(str(unit_amount))
                )
                amount_booked += ccpd.amount
            ccpd.save(user=self.user)
            amount_booked += ccpd.amount
            list_ccpd.append(ccpd)
        return list_ccpd

    def __get_policy(self, insuree, date_valid_from, date_valid_to, product):

        # get all policies related to the product and insuree
        policies = (
            Policy.objects.filter(
                product=product,
                insuree_policies__insuree=insuree,
                expiry_date__gte=date_valid_from,
            )
            .order_by("start_date")
            .distinct()
        )
        policy_output = list(policies)
        date_ranges = [(p.start_date, p.expiry_date,) for p in policies]

        missing_coverage = subtract_date_ranges(
            (
                date_valid_from,
                date_valid_to,
            ),
            date_ranges,
        )
        if missing_coverage:
            policy_created, last_date_covered = self.create_contract_details_policies(
                insuree, product, missing_coverage
            )
            if policy_created is not None and len(policy_created) > 0:
                policy_output += policy_created
        return policy_output

    def create_contract_details_policies(
        self, insuree, product, missing_coverage
    ):
        # create policy for insuree familly
        # TODO Policy with status - new open=32 in policy-be_py module
        policy_output = []
        sorted_list = sorted(missing_coverage, key=lambda x: x[0])

        last_date_covered = sorted_list[0][0]
        date_valid_to = sorted_list[-1][1]

        while last_date_covered < date_valid_to:
            expiry_date = last_date_covered + relativedelta(
                months=product.insurance_period
            )
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
    def create_contribution(self, contract_contribution_plan_details):
        try:
            dict_representation = {}
            contribution_list = []
            from core import datetime

            now = datetime.datetime.now()
            for ccpd in contract_contribution_plan_details["contribution_plan_details"]:
                # contract_details = ContractDetailsModel.objects.get(
                #    id=f"{ccpd['contract_details']}"
                # )
                # create the contributions based on the ContractContributionPlanDetails
                if ccpd.contribution is None:
                    contribution = Premium.objects.create(
                        **{
                            "policy": ccpd.policy,
                            "amount": ccpd.amount,
                            "audit_user_id": self.user._u.audit_user_id,
                            "pay_date": now,
                            # TODO Temporary value pay_type - I have to get to know about this field what should be here
                            #  also ask about audit_user_id and pay_date value
                            "pay_type": " ",
                            "receipt": str(uuid.uuid4()),
                        }
                    )

                    ccpd.contribution = contribution
                    ccpd.save(user=self.user)
                    contribution_record = model_to_dict(contribution)
                    contribution_list.append(contribution_record)
                    dict_representation["contributions"] = contribution_list
                else:
                    pass
            return _output_result_success(dict_representation=dict_representation)
        except Exception as exc:
            return _output_exception(
                model_name="ContractContributionPlanDetails",
                method="createContribution",
                exception=exc,
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
            with transaction.atomic():
                p = update_or_create_payment(data=payment, user=self.user)
                dict_representation = model_to_dict(p)
                dict_representation["id"], dict_representation["uuid"] = (p.id, p.uuid)
                if payment_details:
                    for payment_detail in payment_details:
                        pd = PaymentDetail.objects.create(
                            payment=p,
                            audit_user_id=-1,
                            validity_from=now,
                            product_code=payment_detail["product_code"],
                            insurance_number=payment_detail["insurance_number"],
                            expected_amount=payment_detail["expected_amount"],
                            premium=payment_detail["premium"],
                        )
                        pd_record = model_to_dict(pd)
                        pd_record["id"] = pd.id
                        payment_list.append(pd_record)
            dict_representation["payment_details"] = payment_list
            return _output_result_success(dict_representation=dict_representation)
        except Exception as exc:
            return _output_exception(
                model_name="Payment", method="createPayment", exception=exc
            )

    def collect_payment_details(self, contract_contribution_plan_details):
        payment_details_data = []
        for ccpd in contract_contribution_plan_details:
            product_code = ccpd.contribution_plan.benefit_plan.code
            insurance_number = ccpd.contract_details.insuree.chf_id
            contribution = ccpd.contribution
            expected_amount = ccpd.amount
            payment_details_data.append(
                {
                    "product_code": product_code,
                    "insurance_number": insurance_number,
                    "expected_amount": expected_amount,
                    "premium": contribution,
                }
            )
        return payment_details_data


class ContractToInvoiceService(object):

    def __init__(self, user):
        self.user = user

    @classmethod
    @register_service_signal("create_invoice_from_contract")
    def create_invoice(self, instance, convert_to="Invoice", **kwargs):
        """run convert the ContractContributionPlanDetails of the contract to invoice lines"""
        pass


def _output_exception(model_name, method, exception):
    logger.debug(exception)
    return {
        "success": False,
        "message": f"Failed to {method} {model_name}",
        "detail": f"{exception}",
        "data": traceback.format_exc() if settings.DEBUG else "",
    }


def _output_result_success(dict_representation, object_list=False):
    return {
        "success": True,
        "message": "Ok",
        "detail": "",
        "data": (
            json.loads(json.dumps(dict_representation, cls=DjangoJSONEncoder))
            if not object_list
            else dict_representation
        ),
    }


def _save_json_external(user_id, datetime, message):
    return {
        "comments": [
            {"From": "Portal/webapp", "user": user_id, "date": datetime, "msg": message}
        ]
    }


def _send_email_notify_counter(code, name, contact_name, email):
    try:
        email_to_send = send_mail(
            subject="Contract counter notification",
            message=get_message_counter_contract(
                language=settings.LANGUAGE_CODE.split("-")[0],
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
        return ValueError("Invalid header found.")


def check_unique_code(code):
    if ContractModel.objects.filter(code=code, is_deleted=False).exists():
        return [{"message": _("Contract code %s already exists" % code)}]
    return []


def subtract_date_ranges(main_range, date_ranges):
    main_start, main_end = main_range
    result = []
    current = main_start

    # Sort the date ranges
    sorted_ranges = sorted(date_ranges, key=lambda x: x[0])

    for start, end in sorted_ranges:
        # If there's a gap before the current range, add it to the result
        if current < start:
            result.append((current, min(start, main_end)))

        # Move the current pointer
        current = max(current, end)

        # If we've covered the entire main range, break
        if current >= main_end:
            break

    # If there's remaining uncovered time after the last range, add it
    if current < main_end:
        result.append((current, main_end))

    return result
