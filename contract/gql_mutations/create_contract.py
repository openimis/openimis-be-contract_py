from contract.gql_mutations import ContractInputType
from contract.gql_mutations.utils import update_or_create_contract
from contract.models import Contract

from .base_mutation import BaseContractMutation
from core.utils import TimeUtils
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError, PermissionDenied


class CreateContractMutation(BaseContractMutation):
    _mutation_class = "CreateContractMutation"

    class Input(ContractInputType):
        pass

    @classmethod
    def _validate_mutation(cls, user, **data):
        if type(user) is AnonymousUser or not user.id:
            raise ValidationError("mutation.authentication_required")
        # if not user.has_perms(ContractConfig.gql_mutation_create_contract_perms):
        #     raise PermissionDenied(_("unauthorized"))

    @classmethod
    def _mutate(cls, user, **data):
        data['policy_holder'] = user.id_for_audit
        data['status'] = Contract.STATUS_ENTERED  # TODO: Determine all possible statuses for contract ConfigEnum
        data['validity_from'] = TimeUtils.now()
        data['date_created'] = TimeUtils.now()

        if "client_mutation_id" in data:
            data.pop('client_mutation_id')
        if "client_mutation_label" in data:
            data.pop('client_mutation_label')

        cls.create_contract(data)

    @classmethod
    def create_contract(cls, contract_data):
        contract = Contract.objects.create(**contract_data)
        contract.save()
        return contract
