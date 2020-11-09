from contract.gql.gql_mutations import ContractContributionPlanDetailsInputType
from contract.gql.gql_mutations.base_mutation import BaseMutation, BaseCreateMutationMixin, BaseDeleteMutationMixin, \
    BaseUpdateMutationMixin
from contract.models import ContractContributionPlanDetails


class CreateContractContributionPlanDetailsMutation(BaseMutation, BaseCreateMutationMixin):
    _mutation_class = "ContractMutation"
    _model = ContractContributionPlanDetails

    class Input(ContractContributionPlanDetailsInputType):
        pass


class DeleteContractContributionPlanDetailsMutation(BaseMutation, BaseDeleteMutationMixin):
    _mutation_class = "ContractMutation"
    _model = ContractContributionPlanDetails

    class Input(ContractContributionPlanDetailsInputType):
        pass


class UpdateContractContributionPlanDetailsMutation(BaseMutation, BaseUpdateMutationMixin):
    _mutation_class = "ContractMutation"
    _model = ContractContributionPlanDetails

    class Input(ContractContributionPlanDetailsInputType):
        pass