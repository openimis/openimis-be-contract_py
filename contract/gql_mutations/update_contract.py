from contract.gql_mutations import ContractInputType, ContractNotExistException
from contract.gql_mutations.utils import update_or_create_contract
from contract.models import Contract
from core.schema import OpenIMISMutation
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError, PermissionDenied


class UpdateContractMutation(OpenIMISMutation):
    _mutation_class = "UpdateContractMutation"

    class Input(ContractInputType):
        pass

    @classmethod
    def _validate_mutation(cls, user, **data):
        if type(user) is AnonymousUser or not user.id:
            raise ValidationError("mutation.authentication_required")

        contract_uuid = data['uuid']
        if Contract.objects.filter(uuid=data['uuid']).first() is None:
            raise ContractNotExistException(contract_uuid)
        # if not user.has_perms(ContractConfig.gql_mutation_update_contract_perms):
        #     raise PermissionDenied(_("unauthorized"))

    @classmethod
    def _mutate(cls, user, **data):
        if "client_mutation_id" in data:
            data.pop('client_mutation_id')
        if "client_mutation_label" in data:
            data.pop('client_mutation_label')

        data['policy_holder'] = user.id_for_audit
        contract = Contract.objects.filter(uuid=data['uuid']).first()
        [setattr(contract, key, data[key]) for key in data]
        cls.update_contract(contract)

    @classmethod
    def update_contract(cls, contract):
        contract.save_history()
        contract.save()
        return contract
