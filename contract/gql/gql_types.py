import graphene
from core import prefix_filterset, ExtendedConnection
from graphene_django import DjangoObjectType
from contract.models import Contract, ContractDetails, ContractContributionPlanDetails
from policyholder.gql.gql_types import PolicyHolderInsureeGQLType
from contribution_plan.gql.gql_types import ContributionPlanBundleGQLType


class ContractGQLType(DjangoObjectType):

    class Meta:
        model = Contract
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            "id": ["exact"],
            "code": ["exact", "istartswith", "icontains", "iexact"],
            #"amount_from":,
            #"amount_to":,
            "date_payment_due": ["exact", "lt", "lte", "gt", "gte"],
            "state": ["exact"],
            "payment_reference": ["exact", "istartswith", "icontains", "iexact"],
            "amendment": ["exact"],
            "date_created": ["exact", "lt", "lte", "gt", "gte"],
            "date_updated": ["exact", "lt", "lte", "gt", "gte"],
            "date_valid_from": ["exact", "lt", "lte", "gt", "gte"],
            "date_valid_to": ["exact", "lt", "lte", "gt", "gte"],
            "is_deleted": ["exact"],
            "version": ["exact"],
        }

        connection_class = ExtendedConnection

        @classmethod
        def get_queryset(cls, queryset, info):
            return Contract.get_queryset(queryset, info)


class ContractDetailsGQLType(DjangoObjectType):

    class Meta:
        model = ContractDetails
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            "id": ["exact"],
            **prefix_filterset("policy_holder_insuree__", PolicyHolderInsureeGQLType._meta.filter_fields),
            **prefix_filterset("contribution_plan_bundle__", ContributionPlanBundleGQLType._meta.filter_fields),
            "date_created": ["exact", "lt", "lte", "gt", "gte"],
            "date_updated": ["exact", "lt", "lte", "gt", "gte"],
            "is_deleted": ["exact"],
            "version": ["exact"],
        }

        connection_class = ExtendedConnection

        @classmethod
        def get_queryset(cls, queryset, info):
            return ContractDetails.get_queryset(queryset, info)