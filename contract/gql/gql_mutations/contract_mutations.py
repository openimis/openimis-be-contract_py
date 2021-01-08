from core.gql.gql_mutations.base_mutation  import BaseMutation, BaseDeleteMutation
from .mutations import ContractCreateMutationMixin

from contract.models import Contract
from contract.gql.gql_mutations.input_types import ContractCreateInputType


class CreateContractMutation(ContractCreateMutationMixin, BaseMutation):
    _mutation_class = "CreateContractMutation"
    _mutation_module = "contract"
    _model = Contract

    class Input(ContractCreateInputType):
        pass