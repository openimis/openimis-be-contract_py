import graphene
import graphene_django_optimizer as gql_optimizer

from core.schema import OrderedDjangoFilterConnectionField
from contract.models import Contract, ContractDetails, \
    ContractContributionPlanDetails
from contract.gql.gql_types import ContractGQLType, ContractDetailsGQLType, \
    ContractContributionPlanDetailsGQLType

from contract.gql.gql_mutations.contract_mutations import CreateContractMutation, \
    UpdateContractMutation
from contract.gql.gql_mutations.contract_details_mutations import CreateContractDetailsMutation, \
    UpdateContractDetailsMutation, DeleteContractDetailsMutation

from contract.apps import ContractConfig

class Query(graphene.ObjectType):

    contract = OrderedDjangoFilterConnectionField(
        ContractGQLType,
        insuree=graphene.UUID(),
        orderBy=graphene.List(of_type=graphene.String),
    )

    contract_details = OrderedDjangoFilterConnectionField(
        ContractDetailsGQLType,
        orderBy=graphene.List(of_type=graphene.String)
    )

    contract_contribution_plan_details = OrderedDjangoFilterConnectionField(
        ContractContributionPlanDetailsGQLType,
        insuree=graphene.UUID(),
        contributionPlanBundle=graphene.UUID(),
        orderBy=graphene.List(of_type=graphene.String),
    )

    def resolve_contract(self, info, **kwargs):
        if not info.context.user.has_perms(ContractConfig.gql_query_contract_perms):
           raise PermissionError("Unauthorized")

        query = Contract.objects.all()

        insuree = kwargs.get('insuree', None)

        if insuree:
            query = query.filter(
                contractdetails__insuree__uuid=insuree
            )

        return gql_optimizer.query(query.all(), info)

    def resolve_contract_details(self, info, **kwargs):
        if not info.context.user.has_perms(ContractConfig.gql_query_contract_perms):
           raise PermissionError("Unauthorized")

        query = ContractDetails.objects.all()
        return gql_optimizer.query(query.all(), info)

    def resolve_contract_contribution_plan_details(self, info, **kwargs):
        if not info.context.user.has_perms(ContractConfig.gql_query_contract_perms):
           raise PermissionError("Unauthorized")

        query = ContractContributionPlanDetails.objects.all()

        insuree = kwargs.get('insuree', None)
        contribution_plan_bundle = kwargs.get('contributionPlanBundle', None)

        if insuree:
            query = query.filter(
                contract_details__insuree__uuid=insuree
            )

        if contribution_plan_bundle:
            query = query.filter(
                contributionplanbundledetails__contribution_plan_bundle__id=contribution_plan_bundle
            )

        return gql_optimizer.query(query.all(), info)


class Mutation(graphene.ObjectType):
    create_contract = CreateContractMutation.Field()
    update_contract = UpdateContractMutation.Field()

    create_contract_details = CreateContractDetailsMutation.Field()
    update_contract_details = UpdateContractDetailsMutation.Field()
    delete_contract_details = DeleteContractDetailsMutation.Field()