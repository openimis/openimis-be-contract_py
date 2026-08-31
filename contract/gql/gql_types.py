import graphene
from contribution.gql_queries import PremiumGQLType
from contribution_plan.gql.gql_types import (
    ContributionPlanBundleGQLType,
    ContributionPlanGQLType,
)
from core import ExtendedConnection, prefix_filterset, ExtendedRelayConnection
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
    contract_details = graphene.List(lambda: ContractDetailsGQLType)
    contract_contribution_plan_details = graphene.List(
        lambda: ContractContributionPlanDetailsGQLType
    )

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

        connection_class = ExtendedRelayConnection

        @classmethod
        def get_queryset(cls, queryset, info):
            return Contract.get_queryset(queryset, info)

    def resolve_contract_details(self, info):
        loader = getattr(info.context, "dataloaders", {}).get(
            "contract_details_by_contract"
        )
        if loader:
            return loader.load(self.id)

        return (
            ContractDetails.objects
            .filter(contract_id=self.id, is_deleted=False)
            .select_related("insuree", "contribution_plan_bundle")
        )

    def resolve_contract_contribution_plan_details(self, info):
        loader = getattr(info.context, "dataloaders", {}).get(
            "contract_contribution_plan_details_by_contract"
        )
        if loader:
            return loader.load(self.id)

        return (
            ContractContributionPlanDetails.objects
            .filter(contract_details__contract_id=self.id, is_deleted=False)
            .select_related("contract_details", "contribution_plan", "contribution", "policy")
        )

    # amount = graphene.Float()


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
