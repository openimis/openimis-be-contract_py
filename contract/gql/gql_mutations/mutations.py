from core import TimeUtils
from core.schema import OpenIMISMutation
from contract.services import Contract as ContractService
from contract.apps import ContractConfig
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError


class ContractCreateMutationMixin:

    @property
    def _model(self):
        raise NotImplementedError()

    @classmethod
    def _validate_mutation(cls, user, **data):
        if type(user) is AnonymousUser or not user.id or not user.has_perms(ContractConfig.gql_mutation_create_contract_perms):
            raise ValidationError("mutation.authentication_required")

    @classmethod
    def _mutate(cls, user, **data):
        if "client_mutation_id" in data:
            data.pop('client_mutation_id')
        if "client_mutation_label" in data:
            data.pop('client_mutation_label')
        output = cls.create_contract(user=user, contract=data)
        return None if output["success"] else f"Error! - {output['message']}: {output['detail']}"

    @classmethod
    def create_contract(cls, user, contract):
        contract_service = ContractService(user=user)
        output_data = contract_service.create(contract=contract)
        return output_data


class ContractUpdateMutationMixin:

    @property
    def _model(self):
        raise NotImplementedError()

    @classmethod
    def _validate_mutation(cls, user, **data):
        if type(user) is AnonymousUser or not user.id or not user.has_perms(ContractConfig.gql_mutation_update_contract_perms):
            raise ValidationError("mutation.authentication_required")

    @classmethod
    def _mutate(cls, user, **data):
        if "client_mutation_id" in data:
            data.pop('client_mutation_id')
        if "client_mutation_label" in data:
            data.pop('client_mutation_label')
        output = cls.update_contract(user=user, contract=data)
        return None if output["success"] else f"Error! - {output['message']}: {output['detail']}"

    @classmethod
    def update_contract(cls, user, contract):
        contract_service = ContractService(user=user)
        output_data = contract_service.update(contract=contract)
        return output_data