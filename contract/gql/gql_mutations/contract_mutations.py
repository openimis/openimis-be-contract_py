from core.gql.gql_mutations import DeleteInputType
from core.gql.gql_mutations.base_mutation  import BaseMutation, BaseDeleteMutation
from .mutations import ContractCreateMutationMixin, ContractUpdateMutationMixin, \
    ContractDeleteMutationMixin
from contract.models import Contract
from contract.gql.gql_mutations.input_types import ContractCreateInputType, ContractUpdateInputType


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