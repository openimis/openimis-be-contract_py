import graphene
from contribution.gql_queries import PremiumGQLType
from contribution_plan.gql.gql_types import (
    ContributionPlanBundleGQLType,
    ContributionPlanGQLType,
)
from core import ExtendedConnection, prefix_filterset
from graphene_django import DjangoObjectType
from insuree.schema import InsureeGQLType
from policyholder.gql.gql_types import PolicyHolderGQLType

from contract.models import (
    Contract,
    ContractContributionPlanDetails,
    ContractDetails,
    ContractDetailsMutation,
    ContractMutation,
)


class ContractGQLType(DjangoObjectType):

    class Meta:
        model = Contract
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            "id": ["exact"],
            "code": ["exact", "istartswith", "icontains", "iexact"],
            **prefix_filterset(
                "policy_holder__", PolicyHolderGQLType._meta.filter_fields
            ),
            "amount_notified": ["exact", "lt", "lte", "gt", "gte"],
            "amount_rectified": ["exact", "lt", "lte", "gt", "gte"],
            "amount_due": ["exact", "lt", "lte", "gt", "gte"],
            "date_payment_due": ["exact", "lt", "lte", "gt", "gte"],
            "state": ["exact"],
            "payment_reference": ["exact", "istartswith", "icontains", "iexact"],
            "amendment": ["exact"],
            "date_created": ["exact", "lt", "lte", "gt", "gte"],
            "date_updated": ["exact", "lt", "lte", "gt", "gte"],
            "is_deleted": ["exact"],
            "version": ["exact"],
        }

        connection_class = ExtendedConnection

        @classmethod
        def get_queryset(cls, queryset, info):
            return Contract.get_queryset(queryset, info)

    amount = graphene.Float()


class ContractDetailsGQLType(DjangoObjectType):

    class Meta:
        model = ContractDetails
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            "id": ["exact"],
            **prefix_filterset("contract__", ContractGQLType._meta.filter_fields),
            **prefix_filterset("insuree__", InsureeGQLType._meta.filter_fields),
            **prefix_filterset(
                "contribution_plan_bundle__",
                ContributionPlanBundleGQLType._meta.filter_fields,
            ),
            "date_created": ["exact", "lt", "lte", "gt", "gte"],
            "date_updated": ["exact", "lt", "lte", "gt", "gte"],
            "is_deleted": ["exact"],
            "version": ["exact"],
        }

        connection_class = ExtendedConnection

        @classmethod
        def get_queryset(cls, queryset, info):
            return ContractDetails.get_queryset(queryset, info)


class ContractContributionPlanDetailsGQLType(DjangoObjectType):

    class Meta:
        model = ContractContributionPlanDetails
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            "id": ["exact"],
            **prefix_filterset(
                "contract_details__", ContractDetailsGQLType._meta.filter_fields
            ),
            **prefix_filterset(
                "contribution_plan__", ContributionPlanGQLType._meta.filter_fields
            ),
            **prefix_filterset("contribution__", PremiumGQLType._meta.filter_fields),
            "date_created": ["exact", "lt", "lte", "gt", "gte"],
            "date_updated": ["exact", "lt", "lte", "gt", "gte"],
            "is_deleted": ["exact"],
            "version": ["exact"],
        }

        connection_class = ExtendedConnection

        @classmethod
        def get_queryset(cls, queryset, info):
            return ContractContributionPlanDetails.get_queryset(queryset, info)


class ContractMutationGQLType(DjangoObjectType):
    class Meta:
        model = ContractMutation


class ContractDetailsMutationGQLType(DjangoObjectType):
    class Meta:
        model = ContractDetailsMutation
