from core.gql.gql_mutations import DeleteInputType
from core.gql.gql_mutations.base_mutation  import BaseMutation, BaseDeleteMutation
from .mutations import ContractCreateMutationMixin, ContractUpdateMutationMixin, \
    ContractDeleteMutationMixin, ContractSubmitMutationMixin, \
    ContractApproveMutationMixin, ContractCounterMutationMixin
from contract.models import Contract
from contract.gql.gql_mutations.input_types import ContractCreateInputType, ContractUpdateInputType, \
    ContractSubmitInputType, ContractApproveInputType, ContractCounterInputType


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


class CounterContractMutation(ContractCounterMutationMixin, BaseMutation):
    _mutation_class = "CounterContractMutation"
    _mutation_module = "contract"
    _model = Contract

    class Input(ContractCounterInputType):
        pass