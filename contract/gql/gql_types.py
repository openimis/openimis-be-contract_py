import graphene
from core import ExtendedConnection, prefix_filterset
from graphene_django import DjangoObjectType

from contract.models import Contract, ContractDetails, ContractContributionPlanDetails
from policyholder.qgl import PolicyHolderGQLType, PolicyHolderInsureeGQLType
from contribution_plan.gql import ContributionPlanGQLType, ContributionPlanBundleGQLType


class ContractGQLType(DjangoObjectType):
    class Meta:
        model = Contract
        exclude_fields = ('row_id',)
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            "uuid": ["exact"],
            "version": ["exact"],

            **prefix_filterset("policy_holder__", PolicyHolderGQLType._meta.filter_fields),

            "amount_notified": ["exact", "lt", "lte", "gt", "gte"],
            "amount_rectified": ["exact", "lt", "lte", "gt", "gte"],
            "amount_due": ["exact", "lt", "lte", "gt", "gte"],

            "payment_due_date": ["exact", "lt", "lte", "gt", "gte"],
            "status": ["exact"],
            "payment_reference": ["exact", "istartswith", "icontains", "iexact"],

            "date_created": ["exact", "lt", "lte", "gt", "gte"],
            "date_updated": ["exact", "lt", "lte", "gt", "gte"],

            "user_created": ["exact"],
            "user_updated": ["exact"],

            "contract_from": ["exact", "lt", "lte", "gt", "gte"],
            "contract_to": ["exact", "lt", "lte", "gt", "gte"]
        }

        connection_class = ExtendedConnection

    @classmethod
    def get_queryset(cls, queryset, info):
        return Contract.get_queryset(queryset, info)


class ContractDetailsGQLType(DjangoObjectType):

    class Meta:
        model = ContractDetails
        exclude_fields = ('row_id',)
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            "uuid": ["exact"],
            **prefix_filterset("contract__", ContractGQLType._meta.filter_fields),
            **prefix_filterset("policy_holder_insuree__", PolicyHolderInsureeGQLType._meta.filter_fields),
            **prefix_filterset("contribution_plan_bundle__", ContributionPlanBundleGQLType._meta.filter_fields),

            "date_created": ["exact", "lt", "lte", "gt", "gte"],
            "date_updated": ["exact", "lt", "lte", "gt", "gte"],

            "user_created": ["exact"],
            "user_updated": ["exact"],
        }

        connection_class = ExtendedConnection

    @classmethod
    def get_queryset(cls, queryset, info):
        return ContractDetails.get_queryset(queryset, info)


class ContractContributionPlanDetailsGQLType(DjangoObjectType):

    class Meta:
        model = ContractContributionPlanDetails
        exclude_fields = ('row_id',)
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            "uuid": ["exact"],
            "version": ["exact"],
            **prefix_filterset("contribution_plan__", ContributionPlanGQLType._meta.filter_fields),
            **prefix_filterset("contract_details__", ContractDetailsGQLType._meta.filter_fields),

            "date_created": ["exact", "lt", "lte", "gt", "gte"],
            "date_updated": ["exact", "lt", "lte", "gt", "gte"],

            "user_created": ["exact"],
            "user_updated": ["exact"],
        }

        connection_class = ExtendedConnection

    @classmethod
    def get_queryset(cls, queryset, info):
        return ContractContributionPlanDetails.get_queryset(queryset, info)
