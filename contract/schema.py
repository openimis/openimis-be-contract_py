import graphene
import graphene_django_optimizer as gql_optimizer

from core.schema import OrderedDjangoFilterConnectionField
from contract.models import Contract, ContractDetails, \
    ContractContributionPlanDetails
from contract.gql.gql_types import ContractGQLType, ContractDetailsGQLType, \
    ContractContributionPlanDetailsGQLType


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
        query = Contract.objects.all()

        insuree = kwargs.get('insuree', None)

        if insuree:
            query = query.filter(
                contractdetails__insuree__uuid=insuree
            )

        return gql_optimizer.query(query.all(), info)

    def resolve_contract_details(self, info, **kwargs):
        query = ContractDetails.objects.all()
        return gql_optimizer.query(query.all(), info)

    def resolve_contract_contribution_plan_details(self, info, **kwargs):
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