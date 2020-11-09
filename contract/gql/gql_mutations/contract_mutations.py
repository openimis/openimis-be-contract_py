from contract.gql.gql_mutations import ContractInputType
from contract.gql.gql_mutations.base_mutation import BaseMutation, BaseCreateMutationMixin, BaseSubmitMutationMixin, \
    BaseUpdateMutationMixin, BaseDeleteMutationMixin
from contract.models import Contract


class CreateContractMutation(BaseMutation, BaseCreateMutationMixin):
    _mutation_class = "ContractMutation"
    _model = Contract

    class Input(ContractInputType):
        pass


class SubmitContractMutation(BaseMutation, BaseSubmitMutationMixin):
    _mutation_class = "ContractMutation"
    _model = Contract

    class Input(ContractInputType):
        pass


class UpdateContractMutation(BaseMutation, BaseUpdateMutationMixin):
    _mutation_class = "ContractMutation"
    _model = Contract

    class Input(ContractInputType):
        pass


class DeleteContractMutation(BaseMutation, BaseDeleteMutationMixin):
    _mutation_class = "ContractMutation"
    _model = Contract

    class Input(ContractInputType):
        pass
