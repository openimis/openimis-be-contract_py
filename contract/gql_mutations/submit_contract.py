from contract.gql_mutations import ContractInputType, ContractNotExistException, ContractValidationException
from contract.gql_mutations.utils import update_or_create_contract
from contract.models import Contract

from .base_mutation import BaseContractMutation
from core.utils import TimeUtils
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError, PermissionDenied


class SubmitContractMutation(BaseContractMutation):
    _mutation_class = "SubmitClaimsMutation"

    class Input(ContractInputType):
        pass

    @classmethod
    def async_mutate(cls, user, **data):
        output = []
        for contract_uuid in data["uuids"]:
            submission_result = super(SubmitContractMutation, cls).async_mutate(user, contract_uuid=contract_uuid)
            output += submission_result
        return output

    @classmethod
    def _validate_mutation(cls, user, **data):
        if type(user) is AnonymousUser or not user.id:
            raise ValidationError("mutation.authentication_required")
        # if not user.has_perms(ContractConfig.gql_mutation_submit_contract_perms):
        #     raise PermissionDenied(_("unauthorized"))

    @classmethod
    def _mutate(cls, user, **data):
        return cls.submit_contract_by_uuid(data['contract_uuid'])

    @classmethod
    def submit_contract_by_uuid(cls, contract_uuid):
        contract = Contract.objects.filter(uuid=contract_uuid).first()

        if contract is None:
            raise ContractNotExistException(contract_uuid)
        else:
            cls.submit_contract(contract)

    @classmethod
    def submit_contract(cls, contract: Contract):
        cls.validate_contract(contract)
        contract.save_history()

    @classmethod
    def validate_contract(cls, contract: Contract):
        # TODO: Specify the validation criteria for the contract
        errors = []

        if contract.policy_holder is None:
            contract.status = Contract.STATUS_REJECTED
            errors.append("Policy Holder not defined")

        if errors:
            raise ContractValidationException(contract, errors)
        return True

