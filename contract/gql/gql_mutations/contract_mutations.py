from core.gql.gql_mutations import DeleteInputType, mutation_on_uuids_from_filter_business_model
from core.gql.gql_mutations.base_mutation  import BaseMutation, BaseDeleteMutation
from .mutations import ContractCreateMutationMixin, ContractUpdateMutationMixin, \
    ContractDeleteMutationMixin, ContractSubmitMutationMixin, \
    ContractApproveMutationMixin, ContractCounterMutationMixin, \
    ContractAmendMutationMixin, ContractRenewMutationMixin, ContractCreateInvoiceMutationMixin
from contract.models import Contract
from contract.gql.gql_types import ContractGQLType
from contract.gql.gql_mutations.input_types import ContractCreateInputType, ContractUpdateInputType, \
    ContractSubmitInputType, ContractApproveInputType, ContractCounterInputType, \
    ContractApproveBulkInputType, ContractAmendInputType, ContractRenewInputType, \
    ContractCounterBulkInputType, ContractCreateInvoiceBulkInputType
from contract.tasks import approve_contracts, counter_contracts, create_invoice_from_contracts
from contract.exceptions import CeleryWorkerError
from kombu.exceptions import OperationalError


class CreateContractMutation(ContractCreateMutationMixin, BaseMutation):
    _mutation_class = "CreateContractMutation"
    _mutation_module = "contract"
    _model = Contract

    class Input(ContractCreateInputType):
        pass


class UpdateContractMutation(ContractUpdateMutationMixin, BaseMutation):
    _mutation_class = "UpdateContractMutation"
    _mutation_module = "contract"
    _model = Contract

    class Input(ContractUpdateInputType):
        pass


class DeleteContractMutation(ContractDeleteMutationMixin, BaseDeleteMutation):
    _mutation_class = "DeleteContractMutation"
    _mutation_module = "contract"
    _model = Contract

    class Input(DeleteInputType):
        pass


class SubmitContractMutation(ContractSubmitMutationMixin, BaseMutation):
    _mutation_class = "SubmitContractMutation"
    _mutation_module = "contract"
    _model = Contract

    class Input(ContractSubmitInputType):
        pass


class ApproveContractMutation(ContractApproveMutationMixin, BaseMutation):
    _mutation_class = "ApproveContractMutation"
    _mutation_module = "contract"
    _model = Contract

    class Input(ContractApproveInputType):
        pass


class ApproveContractBulkMutation(ContractApproveMutationMixin, BaseMutation):
    _mutation_class = "ApproveContractBulkMutation"
    _mutation_module = "contract"
    _model = Contract

    @classmethod
    @mutation_on_uuids_from_filter_business_model(Contract, ContractGQLType, 'extended_filters', {})
    def async_mutate(cls, user, **data):
        error_message = None
        if "client_mutation_id" in data:
            data.pop('client_mutation_id')
        if "client_mutation_label" in data:
            data.pop('client_mutation_label')
        if "contract_uuids" in data or "uuids" in data:
            error_message = cls.approve_contracts(user=user, contracts=data)
        return error_message

    def _check_celery_status(cls):
        try:
            from openIMIS.celery import app as celery_app
            connection = celery_app.broker_connection().ensure_connection(max_retries=3)
            if not connection:
                raise CeleryWorkerError("Celery worker not found. Please, contact your system administrator.")
        except (IOError, OperationalError) as e:
            raise CeleryWorkerError(
                F"Celery connection has failed. Error: {e} \n Please, contact your system administrator.")
    @classmethod
    def approve_contracts(cls, user, contracts):
        try:
            cls._check_celery_status(cls)
        except CeleryWorkerError as e:
            return F"Celery connection has failed. Please, contact your system administrator."
        if "uuids" in contracts:
            contracts["uuids"] = list(contracts["uuids"].values_list("id", flat=True))
            approve_contracts.delay(user_id=f'{user.id}', contracts=contracts["uuids"])
        else:
            if "contract_uuids" in contracts:
                approve_contracts.delay(user_id=f'{user.id}', contracts=contracts["contract_uuids"])

    class Input(ContractApproveBulkInputType):
        pass


class CounterContractMutation(ContractCounterMutationMixin, BaseMutation):
    _mutation_class = "CounterContractMutation"
    _mutation_module = "contract"
    _model = Contract

    class Input(ContractCounterInputType):
        pass


class ContractCreateInvoiceBulkMutation(ContractCreateInvoiceMutationMixin, BaseMutation):
    _mutation_class = "ContractCreateInvoiceBulkMutation"
    _mutation_module = "contract"
    _model = Contract

    @classmethod
    @mutation_on_uuids_from_filter_business_model(Contract, ContractGQLType, 'extended_filters', {})
    def async_mutate(cls, user, **data):
        if "client_mutation_id" in data:
            data.pop('client_mutation_id')
        if "client_mutation_label" in data:
            data.pop('client_mutation_label')
        if "contract_uuids" in data or "uuids" in data:
            cls.create_contract_invoice(user=user, contracts=data)
        return None

    @classmethod
    def create_contract_invoice(cls, user, contracts):
        if "uuids" in contracts:
            contracts["uuids"] = list(contracts["uuids"].values_list("id", flat=True))
            create_invoice_from_contracts.delay(user_id=f'{user.id}', contracts=contracts["uuids"])
        else:
            if "contract_uuids" in contracts:
                create_invoice_from_contracts.delay(user_id=f'{user.id}', contracts=contracts["contract_uuids"])

    class Input(ContractCreateInvoiceBulkInputType):
        pass


class CounterContractBulkMutation(ContractCounterMutationMixin, BaseMutation):
    _mutation_class = "CounterContractBulkMutation"
    _mutation_module = "contract"
    _model = Contract

    @classmethod
    @mutation_on_uuids_from_filter_business_model(Contract, ContractGQLType, 'extended_filters', {})
    def async_mutate(cls, user, **data):
        if "client_mutation_id" in data:
            data.pop('client_mutation_id')
        if "client_mutation_label" in data:
            data.pop('client_mutation_label')
        if "contract_uuids" in data or "uuids" in data:
            cls.counter_contracts(user=user, contracts=data)
        return None

    @classmethod
    def counter_contracts(cls, user, contracts):
        if "uuids" in contracts:
            contracts["uuids"] = list(contracts["uuids"].values_list("id", flat=True))
            counter_contracts.delay(user_id=f'{user.id}', contracts=contracts["uuids"])
        else:
            if "contract_uuids" in contracts:
                counter_contracts.delay(user_id=f'{user.id}', contracts=contracts["contract_uuids"])

    class Input(ContractCounterBulkInputType):
        pass


class AmendContractMutation(ContractAmendMutationMixin, BaseMutation):
    _mutation_class = "AmendContractMutation"
    _mutation_module = "contract"
    _model = Contract

    class Input(ContractAmendInputType):
        pass


class RenewContractMutation(ContractRenewMutationMixin, BaseMutation):
    _mutation_class = "RenewContractMutation"
    _mutation_module = "contract"
    _model = Contract

    class Input(ContractRenewInputType):
        pass