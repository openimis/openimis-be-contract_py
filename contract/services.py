import core
import json

from django.contrib.auth.models import AnonymousUser
from django.core.serializers.json import DjangoJSONEncoder
from django.forms.models import model_to_dict

from contract.models import Contract as ContractModel, \
    ContractDetails as ContractDetailsModel, \
    ContractContributionPlanDetails as ContractContributionPlanDetailsModel

from policyholder.models import PolicyHolderInsuree
from contribution_plan.models import ContributionPlanBundleDetails


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
            # create contract
            c = ContractModel(**contract)
            c.state = ContractModel.STATE_DRAFT
            c.save(username=self.user.username)
            uuid_string = str(c.id)
            date_updated = c.date_updated
            # check if the PH is set
            if contract["policy_holder"]:
                # run service updateFromPHInsuree
                phi = PolicyHolderInsuree.objects.get(id=contract["policy_holder"])
                cd = ContractDetails(user=self.user)
                result_update_from_phi = cd.update_from_ph_insuree(
                    contract_details={
                        "contract_id": uuid_string,
                        "insuree_id": phi.insuree.id,
                        "contribution_plan_bundle_id": str(phi.contribution_plan_bundle.id),
                    }
                )
                # get contribution plan
                cp = ContributionPlanBundleDetails.objects.get(
                    contribution_plan__id=phi.contribution_plan_bundle.id
                )
                ccpd = ContractContributionPlanDetails(user=self.user)
                result_contract_valuation = ccpd.contract_valuation(
                    save=False,
                    contract_contribution_plan_details={
                        "contract_details_id": str(result_update_from_phi["data"]["id"]),
                        "contribution_plan_id": str(cp.id),
                        "policy_id": phi.policy.id
                    }
                )
                # save the amopunt rectified and decrease version to 1
                c.version = 1
                c.date_updated = c.date_updated
                c.amount_rectified = result_contract_valuation["data"]["total_amount"]
                c.save(username=self.user.username)
            dict_representation = model_to_dict(c)
            dict_representation['id'], dict_representation['uuid'] = (str(uuid_string), str(uuid_string))
        except Exception as exc:
            return _output_exception(model_name="Contract", method="create", exception=exc)

    def submit(self, submit):
        pass

    def amend(self, submit):
        pass

    def update(self, contract):
        pass

    def delete(self, contract):
        pass


class ContractDetails(object):

    def __init__(self, user):
        self.user = user

    @check_authentication
    def update_from_ph_insuree(self, contract_details):
        try:
            cd = ContractDetailsModel(**contract_details)
            cd.save(self.user)
            uuid_string = str(contract_details.id)
            dict_representation = model_to_dict(contract_details)
            dict_representation["id"], dict_representation["uuid"] = (str(uuid_string), str(uuid_string))
        except Exception as exc:
            return _output_exception(model_name="ContractDetails", method="updateFromPHInsuree", exception=exc)
        return _output_result_success(dict_representation=dict_representation)


class ContractContributionPlanDetails(object):

    def __init__(self, user):
        self.user = user

    @check_authentication
    def contract_valuation(self, save, contract_contribution_plan_details):
        try:
            ccpd = ContractContributionPlanDetailsModel(
                **contract_contribution_plan_details
            )
            if save:
                ccpd.save(self.user)
            uuid_string = str(contract_details.id)
            dict_representation = model_to_dict(ccpd)
            # temporary value until calculation module be developed
            dict_representation["total_amount"] = 250
        except Exception as exc:
            return _output_exception(
                model_name="ContractContributionPlanDetails",
                method="contractValuation",
                exception=exc
            )
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