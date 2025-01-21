from core.gql.gql_mutations import ObjectNotExistException
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.forms.models import model_to_dict
from django.utils.translation import gettext as _

from contract.apps import ContractConfig
from contract.models import Contract, ContractMutation
from contract.services import (
    Contract as ContractService,
    ContractDetails as ContractDetailsService,
    ContractToInvoiceService,
    _output_result_success,
    _output_exception
)


class ContractCreateMutationMixin:

    @property
    def _model(self):
        raise NotImplementedError()

    @classmethod
    def _validate_mutation(cls, user, **data):
        if type(user) is AnonymousUser or not user.id:
            raise ValidationError("mutation.authentication_required")

    @classmethod
    def _mutate(cls, user, **data):
        client_mutation_id = data.get("client_mutation_id")
        if "client_mutation_id" in data:
            data.pop("client_mutation_id")
        if "client_mutation_label" in data:
            data.pop("client_mutation_label")
        output = cls.create_contract(user=user, contract=data)
        if output["success"]:
            contract = Contract.objects.get(id=output["data"]["id"])
            ContractMutation.object_mutated(
                user, client_mutation_id=client_mutation_id, contract=contract
            )
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
        if type(user) is AnonymousUser or not user.id:
            raise ValidationError("mutation.authentication_required")

        
    @classmethod
    def _mutate(cls, user, **data):
        if "client_mutation_id" in data:
            data.pop("client_mutation_id")
        if "client_mutation_label" in data:
            data.pop("client_mutation_label")
        output = cls.update_contract(user=user, contract=data)
        return (
            None
            if output["success"]
            else f"Error! - {output['message']}: {output['detail']}"
        )

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
        return (
            None
            if output["success"]
            else f"Error! - {output['message']}: {output['detail']}"
        )

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
        if type(user) is AnonymousUser or not user.id:
            raise ValidationError("mutation.authentication_required")

    @classmethod
    def _mutate(cls, user, **data):
        if "client_mutation_id" in data:
            data.pop("client_mutation_id")
        if "client_mutation_label" in data:
            data.pop("client_mutation_label")
        output = cls.submit_contract(user=user, contract=data)
        return (
            None
            if output["success"]
            else f"Error! - {output['message']}: {output['detail']}"
        )

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
        if type(user) is AnonymousUser or not user.id:
            raise ValidationError("mutation.authentication_required")

    @classmethod
    def _mutate(cls, user, **data):
        if "client_mutation_id" in data:
            data.pop("client_mutation_id")
        if "client_mutation_label" in data:
            data.pop("client_mutation_label")
        output = cls.approve_contract(user=user, contract=data)
        return (
            None
            if output["success"]
            else f"Error! - {output['message']}: {output['detail']}"
        )

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
        if type(user) is AnonymousUser or not user.id:
            raise ValidationError("mutation.authentication_required")

    @classmethod
    def _mutate(cls, user, **data):
        if "client_mutation_id" in data:
            data.pop("client_mutation_id")
        if "client_mutation_label" in data:
            data.pop("client_mutation_label")
        output = cls.counter_contract(user=user, contract=data)
        return (
            None
            if output["success"]
            else f"Error! - {output['message']}: {output['detail']}"
        )

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
        if type(user) is AnonymousUser or not user.id:
            raise ValidationError("mutation.authentication_required")

    @classmethod
    def _mutate(cls, user, **data):
        client_mutation_id = data.get("client_mutation_id")
        if "client_mutation_id" in data:
            data.pop("client_mutation_id")
        if "client_mutation_label" in data:
            data.pop("client_mutation_label")
        output = cls.amend_contract(user=user, contract=data)
        if output["success"]:
            contract = Contract.objects.get(id=output["data"]["id"])
            ContractMutation.object_mutated(
                user, client_mutation_id=client_mutation_id, contract=contract
            )
            return None
        else:
            return f"Error! - {output['message']}: {output['detail']}"

    @classmethod
    def amend_contract(cls, user, contract):
        contract_service = ContractService(user=user)
        output_data = contract_service.amend(contract=contract)
        return output_data


class ContractRenewMutationMixin:

    @property
    def _model(self):
        raise NotImplementedError()

    @classmethod
    def _validate_mutation(cls, user, **data):
        if type(user) is AnonymousUser or not user.id:
            raise ValidationError("mutation.authentication_required")

    @classmethod
    def _mutate(cls, user, **data):
        client_mutation_id = data.get("client_mutation_id")
        if "client_mutation_id" in data:
            data.pop("client_mutation_id")
        if "client_mutation_label" in data:
            data.pop("client_mutation_label")
        output = cls.renew_contract(user=user, contract=data)
        if output["success"]:
            contract = Contract.objects.get(id=output["data"]["id"])
            ContractMutation.object_mutated(
                user, client_mutation_id=client_mutation_id, contract=contract
            )
            return None
        else:
            return f"Error! - {output['message']}: {output['detail']}"

    @classmethod
    def renew_contract(cls, user, contract):
        contract_service = ContractService(user=user)
        output_data = contract_service.renew(contract=contract)
        return output_data


class ContractDetailsFromPHInsureeMutationMixin:

    @property
    def _model(self):
        raise NotImplementedError()

    @classmethod
    def _validate_mutation(cls, user, **data):
        if type(user) is AnonymousUser or not user.id:
            raise ValidationError("mutation.authentication_required")

    @classmethod
    def _mutate(cls, user, **data):
        if "client_mutation_id" in data:
            data.pop("client_mutation_id")
        if "client_mutation_label" in data:
            data.pop("client_mutation_label")
        output = cls.create_cd_from_ph_insuree(user=user, data=data)
        return (
            None
            if output["success"]
            else f"Error! - {output['message']}: {output['detail']}"
        )

    @classmethod
    def create_cd_from_ph_insuree(cls, user, data):
        contract_details_service = ContractDetailsService(user=user)
        try:
            contract = Contract.get(id=f'{data["contract_id"]}')
            if contract.state not in [
                    Contract.STATE_DRAFT,
                    Contract.STATE_REQUEST_FOR_INFORMATION,
                    Contract.STATE_COUNTER,
            ]:
                raise Exception(
                    _(
                        "You cannot update contract by adding insuree - contract not in updatable state!"
                    )
                )
            contract_details = contract_details_service.get_details_from_ph_insuree(
                contract,
                ph_insuree_id=data["policy_holder_insuree_id"]
            )
            dict_representation = []
            for cd in contract_details:
                uuid_string = f"{cd.id}"
                record = model_to_dict(cd)
                record["id"], record["uuid"] = (
                    uuid_string,
                    uuid_string,
                )
                dict_representation.append(record)
                return _output_result_success(dict_representation)
            else:
                raise Exception(
                    _(
                        "You cannot insuree - is deleted or not enough data to create contract!"
                    )
                )
        except Exception as exc:
            return _output_exception(
                model_name="ContractDetails",
                method="PHInsureToCDetatils",
                exception=exc,
            )


class ContractCreateInvoiceMutationMixin:

    @property
    def _model(self):
        raise NotImplementedError()

    @classmethod
    def _validate_mutation(cls, user, **data):
        if type(user) is AnonymousUser or not user.id:
            raise ValidationError("mutation.authentication_required")

    @classmethod
    def _mutate(cls, user, **data):
        if "client_mutation_id" in data:
            data.pop("client_mutation_id")
        if "client_mutation_label" in data:
            data.pop("client_mutation_label")
        output = cls.create_contract_invoice(user=user, data=data)
        if output["success"]:
            return None
        else:
            return f"Error! - {output['message']}: {output['detail']}"

    @classmethod
    def create_contract_invoice(cls, user, data):
        queryset = Contract.objects.filter(id=data["id"])
        if queryset.count() == 1:
            contract = queryset.first()
            contract_to_invoice_service = ContractToInvoiceService(user=user)
            output_data = contract_to_invoice_service.create_invoice(
                instance=contract, convert_to="InvoiceLine", user=user
            )
            return output_data
