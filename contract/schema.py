import graphene_django_optimizer as gql_optimizer
from contract.gql.gql_mutations.contract_contribution_plan_details import CreateContractContributionPlanDetailsMutation, \
    UpdateContractContributionPlanDetailsMutation, DeleteContractContributionPlanDetailsMutation
from contract.gql.gql_mutations.contract_details_mutations import CreateContractDetailsMutation, \
    DeleteContractDetailsMutation, UpdateContractDetailsMutation
from contract.gql.gql_mutations.contract_mutations import CreateContractMutation, UpdateContractMutation, \
    DeleteContractMutation, SubmitContractMutation

from .gql import ContractGQLType, ContractDetailsGQLType, ContractContributionPlanDetailsGQLType
from contract.models import Contract, ContractDetails, ContractContributionPlanDetails
from core.schema import OrderedDjangoFilterConnectionField
from contract.gql.gql_mutations import *


class Query(graphene.ObjectType):
    contract = OrderedDjangoFilterConnectionField(ContractGQLType)
    contract_details = OrderedDjangoFilterConnectionField(ContractDetailsGQLType)
    contract_contribution_plan_details = OrderedDjangoFilterConnectionField(ContractContributionPlanDetailsGQLType)

    def resolve_contract(self, info, **kwargs):
        query = Contract.objects
        return gql_optimizer.query(query.all(), info)

    def resolve_contract_details(self, info, **kwargs):
        query = ContractDetails.objects
        return gql_optimizer.query(query.all(), info)

    def resolve_contract_contribution_plan_details(self, info, **kwargs):
        query = ContractContributionPlanDetails.objects
        return gql_optimizer.query(query.all(), info)


class Mutation(graphene.ObjectType):
    create_contract = CreateContractMutation.Field()
    update_contract = UpdateContractMutation.Field()
    delete_contract = DeleteContractMutation.Field()
    submit_contract = SubmitContractMutation.Field()

    create_contract_details = CreateContractDetailsMutation.Field()
    update_contract_details = UpdateContractDetailsMutation.Field()
    delete_contract_details = DeleteContractDetailsMutation.Field()

    create_contract_contribution_plan_details = \
        CreateContractContributionPlanDetailsMutation.Field()
    update_contract_contribution_plan_details = \
        UpdateContractContributionPlanDetailsMutation.Field()
    delete_contract_contribution_plan_details = \
        DeleteContractContributionPlanDetailsMutation.Field()
