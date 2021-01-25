from core.gql.gql_mutations import DeleteInputType
from core.gql.gql_mutations.base_mutation import BaseMutation, BaseDeleteMutation, \
    BaseHistoryModelCreateMutationMixin, BaseHistoryModelUpdateMutationMixin, \
    BaseHistoryModelDeleteMutationMixin
from contract.gql.gql_mutations import ContractDetailsCreateInputType, ContractDetailsUpdateInputType
from contract.models import ContractDetails


class CreateContractDetailsMutation(BaseHistoryModelCreateMutationMixin, BaseMutation):
    _mutation_class = "ContractDetailsMutation"
    _mutation_module = "contract"
    _model = ContractDetails

    class Input(ContractDetailsCreateInputType):
        pass


class UpdateContractDetailsMutation(BaseHistoryModelUpdateMutationMixin, BaseMutation):
    _mutation_class = "ContractDetailsMutation"
    _mutation_module = "contract"
    _model = ContractDetails

    class Input(ContractDetailsUpdateInputType):
        pass


class DeleteContractDetailsMutation(BaseHistoryModelDeleteMutationMixin, BaseDeleteMutation):
    _mutation_class = "ContractDetailsMutation"
    _mutation_module = "contract"
    _model = ContractDetails

    class Input(DeleteInputType):
        pass