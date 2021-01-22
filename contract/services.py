import core
import json

from django.db.models.query import QuerySet
from django.contrib.auth.models import AnonymousUser
from django.core.serializers.json import DjangoJSONEncoder
from django.forms.models import model_to_dict

from contract.apps import ContractConfig
from contract.models import Contract as ContractModel, \
    ContractDetails as ContractDetailsModel, \
    ContractContributionPlanDetails as ContractContributionPlanDetailsModel

from policyholder.models import PolicyHolderInsuree
from contribution_plan.models import ContributionPlanBundleDetails


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
            uuid_string = str(c.id)
            # check if the PH is set
            if "policy_holder_id" in contract:
                # run services updateFromPHInsuree and Contract Valuation
                cd = ContractDetails(user=self.user)
                result_ph_insuree = cd.update_from_ph_insuree(contract_details={
                    "policy_holder_id": contract["policy_holder_id"],
                    "contract_id": uuid_string,
                })
                total_amount = self.__evaluate_contract_valuation(
                    contract_details_result=result_ph_insuree,
                )
                c.amount_notified = total_amount
            historical_record = c.history.all().last()
            c.json_ext = json.dumps(_save_json_external(
                user_id=historical_record.user_updated.id,
                datetime=historical_record.date_updated,
                message="create contract status "+str(historical_record.state)
            ), cls=DjangoJSONEncoder)
            c.save(username=self.user.username)
            dict_representation = model_to_dict(c)
            dict_representation['id'], dict_representation['uuid'] = (str(uuid_string), str(uuid_string))
        except Exception as exc:
            return _output_exception(model_name="Contract", method="create", exception=exc)
        return _output_result_success(dict_representation=dict_representation)

    def __evaluate_contract_valuation(self, contract_details_result):
        ccpd = ContractContributionPlanDetails(user=self.user)
        result_contract_valuation = ccpd.contract_valuation(
            contract_contribution_plan_details={
                "contract_details": contract_details_result["data"],
                "save": False,
            }
        )
        return result_contract_valuation["data"]["total_amount"]

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
        except Exception as exc:
            return _output_exception(model_name="ContractModule", method="update", exception=exc)

    def __check_rights_by_status(self, status):
        state = "cannot_update"
        if status in [ContractModel.STATE_DRAFT, ContractModel.STATE_REQUEST_FOR_INFORMATION, ContractModel.STATE_COUNTER]:
           state = "updatable"
        if status == ContractModel.STATE_NEGOTIABLE:
            state = "approvable"
        return state

    def __update_contract_fields(self, contract_input, updated_contract):
        # get the current policy_holder value
        current_policy_holder_id = updated_contract.policy_holder_id
        [setattr(updated_contract, key, contract_input[key]) for key in contract_input]
        updated_contract.save(username=self.user.username)
        # save the communication
        historical_record = updated_contract.history.all().first()
        updated_contract.json_ext = json.dumps(_save_json_external(
            user_id=historical_record.user_updated.id,
            datetime=historical_record.date_updated,
            message="update contract status "+str(historical_record.state)
        ), cls=DjangoJSONEncoder)
        updated_contract.save(username=self.user.username)
        uuid_string = str(updated_contract.id)
        dict_representation = model_to_dict(updated_contract)
        dict_representation["id"], dict_representation["uuid"] = (str(uuid_string), str(uuid_string))
        return dict_representation

    def submit(self, submit):
        pass

    def amend(self, submit):
        pass

    def delete(self, contract):
        pass


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
                #TODO add the validity condition also!
                if phi.is_deleted == False and phi.contribution_plan_bundle:
                    cd = ContractDetailsModel(
                       **{
                           "contract_id": contract_details["contract_id"],
                           "insuree_id": phi.insuree.id,
                           "contribution_plan_bundle_id": str(phi.contribution_plan_bundle.id),
                       }
                    )
                    cd.save(self.user)
                    uuid_string = str(cd.id)
                    dict_representation = model_to_dict(cd)
                    dict_representation["id"], dict_representation["uuid"] = (str(uuid_string), str(uuid_string))
                    dict_representation["policy_id"] = phi.last_policy.id
                    contract_insuree_list.append(dict_representation)
        except Exception as exc:
            return _output_exception(model_name="ContractDetails", method="updateFromPHInsuree", exception=exc)
        return _output_result_success(dict_representation=contract_insuree_list)


class ContractContributionPlanDetails(object):

    def __init__(self, user):
        self.user = user

    @check_authentication
    def contract_valuation(self, contract_contribution_plan_details):
        try:
            dict_representation = {}
            total_amount = 0
            for contract_details in contract_contribution_plan_details["contract_details"]:
                cp = ContributionPlanBundleDetails.objects.filter(
                    contribution_plan_bundle__id=str(contract_details["contribution_plan_bundle"])
                )[0]
                ccpd = ContractContributionPlanDetailsModel(
                    **{
                        "contract_details_id": contract_details["id"],
                        "contribution_plan_id": str(cp.id),
                        "policy_id": contract_details["policy_id"]
                    }
                )
                # TODO here will be a function from calculation module
                #  to count the value for amount. And now temporary value is here
                #  until calculation module be developed
                total_amount += 250
                if contract_contribution_plan_details["save"]:
                   ccpd.save(self.user)
                   uuid_string = str(ccpd.id)
                   dict_representation['id'], dict_representation['uuid'] = (str(uuid_string), str(uuid_string))
        except Exception as exc:
            return _output_exception(
                model_name="ContractContributionPlanDetails",
                method="contractValuation",
                exception=exc
            )
        dict_representation['total_amount'] = total_amount
        return _output_result_success(dict_representation=dict_representation)


@core.comparable
class Payment(object):

    def __init__(self, policy_holder):
        self.policy_holder = policy_holder
        pass

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def submit(self, payment):
        pass

    def create(self, payment):
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
        "detail": str(exception),
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