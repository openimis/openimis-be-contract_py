import graphene
import graphene_django_optimizer as gql_optimizer

from django.db.models import Q

from core.schema import OrderedDjangoFilterConnectionField

from contract.gql.gql_types import ContractGQLType, ContractDetailsGQLType, \
    ContractContributionPlanDetailsGQLType

class Query(graphene.ObjectType):

    contract = OrderedDjangoFilterConnectionField(
        ContractGQLType,
        orderBy=graphene.List(of_type=graphene.String)
    )

    contract_details = OrderedDjangoFilterConnectionField(
        ContractDetailsGQLType,
        orderBy=graphene.List(of_type=graphene.String)
    )

    contract_contribution_plan_details = OrderedDjangoFilterConnectionField(
        ContractContributionPlanDetailsGQLType,
        contribution_plan_bundle=graphene.UUID(),
        orderBy=graphene.List(of_type=graphene.String),
    )

    def resolve_contract(selfself, info, **kwargs):
        pass






