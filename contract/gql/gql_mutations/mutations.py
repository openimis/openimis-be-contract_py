from core import TimeUtils
from core.schema import OpenIMISMutation
from core.gql.gql_mutations import ObjectNotExistException
from contract.services import Contract as ContractService
from contract.models import Contract, ContractMutation
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
        client_mutation_id = data.get("client_mutation_id")
        if "client_mutation_id" in data:
            data.pop('client_mutation_id')
        if "client_mutation_label" in data:
            data.pop('client_mutation_label')
        output = cls.create_contract(user=user, contract=data)
        if output["success"]:
           contract = Contract.objects.get(id=output["data"]["id"])
           ContractMutation.object_mutated(user, client_mutation_id=client_mutation_id, contract=contract)
           return None
        else:
           return f"Error! - {output['message']}: {output['detail']}"

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


class ContractDeleteMutationMixin:
    @property
    def _model(self):
        raise NotImplementedError()

    @classmethod
    def _object_not_exist_exception(cls, obj_uuid):
        raise ObjectNotExistException(cls._model, obj_uuid)

    @classmethod
    def _validate_mutation(cls, user, **data):
        cls._validate_user(user)

    @classmethod
    def _validate_user(cls, user):
        if type(user) is AnonymousUser or not user.id:
            raise ValidationError("mutation.authentication_required")

    @classmethod
    def _mutate(cls, user, uuid):
        output = cls.delete_contract(user=user, contract={"id": uuid})
        return None if output["success"] else f"Error! - {output['message']}: {output['detail']}"

    @classmethod
    def delete_contract(cls, user, contract):
        contract_service = ContractService(user=user)
        output_data = contract_service.delete(contract=contract)
        return output_data


class ContractSubmitMutationMixin:

    @property
    def _model(self):
        raise NotImplementedError()

    @classmethod
    def _validate_mutation(cls, user, **data):
        if type(user) is AnonymousUser or not user.id or not user.has_perms(ContractConfig.gql_mutation_submit_contract_perms):
            raise ValidationError("mutation.authentication_required")

    @classmethod
    def _mutate(cls, user, **data):
        if "client_mutation_id" in data:
            data.pop('client_mutation_id')
        if "client_mutation_label" in data:
            data.pop('client_mutation_label')
        output = cls.submit_contract(user=user, contract=data)
        return None if output["success"] else f"Error! - {output['message']}: {output['detail']}"

    @classmethod
    def submit_contract(cls, user, contract):
        contract_service = ContractService(user=user)
        output_data = contract_service.submit(contract=contract)
        return output_data


class ContractApproveMutationMixin:

    @property
    def _model(self):
        raise NotImplementedError()

    @classmethod
    def _validate_mutation(cls, user, **data):
        if type(user) is AnonymousUser or not user.id or not user.has_perms(ContractConfig.gql_mutation_approve_ask_for_change_contract_perms):
            raise ValidationError("mutation.authentication_required")

    @classmethod
    def _mutate(cls, user, **data):
        if "client_mutation_id" in data:
            data.pop('client_mutation_id')
        if "client_mutation_label" in data:
            data.pop('client_mutation_label')
        output = cls.approve_contract(user=user, contract=data)
        return None if output["success"] else f"Error! - {output['message']}: {output['detail']}"

    @classmethod
    def approve_contract(cls, user, contract):
        contract_service = ContractService(user=user)
        output_data = contract_service.approve(contract=contract)
        return output_data


class ContractCounterMutationMixin:

    @property
    def _model(self):
        raise NotImplementedError()

    @classmethod
    def _validate_mutation(cls, user, **data):
        if type(user) is AnonymousUser or not user.id or not user.has_perms(ContractConfig.gql_mutation_approve_ask_for_change_contract_perms):
            raise ValidationError("mutation.authentication_required")

    @classmethod
    def _mutate(cls, user, **data):
        if "client_mutation_id" in data:
            data.pop('client_mutation_id')
        if "client_mutation_label" in data:
            data.pop('client_mutation_label')
        output = cls.counter_contract(user=user, contract=data)
        return None if output["success"] else f"Error! - {output['message']}: {output['detail']}"

    @classmethod
    def counter_contract(cls, user, contract):
        contract_service = ContractService(user=user)
        output_data = contract_service.counter(contract=contract)
        return output_data


class ContractAmendMutationMixin:

    @property
    def _model(self):
        raise NotImplementedError()

    @classmethod
    def _validate_mutation(cls, user, **data):
        if type(user) is AnonymousUser or not user.id or not user.has_perms(ContractConfig.gql_mutation_amend_contract_perms):
            raise ValidationError("mutation.authentication_required")

    @classmethod
    def _mutate(cls, user, **data):
        if "client_mutation_id" in data:
            data.pop('client_mutation_id')
        if "client_mutation_label" in data:
            data.pop('client_mutation_label')
        output = cls.amend_contract(user=user, contract=data)
        return None if output["success"] else f"Error! - {output['message']}: {output['detail']}"

    @classmethod
    def amend_contract(cls, user, contract):
        contract_service = ContractService(user=user)
        output_data = contract_service.amend(contract=contract)
        return output_data