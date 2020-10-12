from functools import lru_cache

from contract.gql_mutations import ContractInputType, ContractNotExistException
from contract.models import Contract
from core.schema import OpenIMISMutation
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError, PermissionDenied


class DeleteContractMutation(OpenIMISMutation):
    _mutation_class = "DeleteContractMutation"

    class Input(ContractInputType):
        pass

    @classmethod
    def async_mutate(cls, user, **data):
        output = []
        for contract_uuid in data["uuids"]:
            deletion_result = super(DeleteContractMutation, cls).async_mutate(user, contract_uuid=contract_uuid)
            output += deletion_result
        return output

    @classmethod
    def _validate_mutation(cls, user, **data):
        cls._validate_user(user)

    @classmethod
    @lru_cache(1)
    def _validate_user(cls, user):
        if type(user) is AnonymousUser or not user.id:
            raise ValidationError("mutation.authentication_required")
        # if not user.has_perms(ContractConfig.gql_mutation_delete_contract_perms):
        #     raise PermissionDenied(_("unauthorized"))

    @classmethod
    def _mutation(cls, contract_uuid):
        contract = Contract.objects.filter(uuid=contract_uuid).first()

        if contract is None:
            raise ContractNotExistException(contract_uuid)
        else:
            contract.delete_history()
