from core.gql.gql_mutations import DeleteInputType
from core.gql.gql_mutations.base_mutation  import BaseMutation, BaseDeleteMutation
from .mutations import ContractCreateMutationMixin, ContractUpdateMutationMixin, \
    ContractDeleteMutationMixin, ContractSubmitMutationMixin, \
    ContractApproveMutationMixin, ContractCounterMutationMixin, \
    ContractAmendMutationMixin, ContractRenewMutationMixin
from contract.models import Contract
from contract.gql.gql_mutations.input_types import ContractCreateInputType, ContractUpdateInputType, \
    ContractSubmitInputType, ContractApproveInputType, ContractCounterInputType, \
    ContractApproveBulkInputType, ContractAmendInputType, ContractRenewInputType
from contract.tasks import approve_contracts


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
    def _mutate(cls, user, **data):
        if "client_mutation_id" in data:
            data.pop('client_mutation_id')
        if "client_mutation_label" in data:
            data.pop('client_mutation_label')
        if "contract_uuids" in data:
            cls.approve_contracts(user=user, contracts=data["contract_uuids"])
        return None

    @classmethod
    def approve_contracts(cls, user, contracts):
        approve_contracts.delay(user_id=f'{user.id}', contracts=contracts)

    class Input(ContractApproveBulkInputType):
        pass


class CounterContractMutation(ContractCounterMutationMixin, BaseMutation):
    _mutation_class = "CounterContractMutation"
    _mutation_module = "contract"
    _model = Contract

    class Input(ContractCounterInputType):
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