from contract.gql.gql_mutations import ContractDetailsInputType
from contract.gql.gql_mutations.base_mutation import BaseMutation, BaseCreateMutationMixin, BaseDeleteMutationMixin, \
    BaseUpdateMutationMixin
from contract.models import ContractDetails


class CreateContractDetailsMutation(BaseMutation, BaseCreateMutationMixin):
    _mutation_class = "ContractMutation"
    _model = ContractDetails

    class Input(ContractDetailsInputType):
        pass


class DeleteContractDetailsMutation(BaseMutation, BaseDeleteMutationMixin):
    _mutation_class = "ContractMutation"
    _model = ContractDetails

    class Input(ContractDetailsInputType):
        pass


class UpdateContractDetailsMutation(BaseMutation, BaseUpdateMutationMixin):
    _mutation_class = "ContractMutation"
    _model = ContractDetails

    class Input(ContractDetailsInputType):
        pass
