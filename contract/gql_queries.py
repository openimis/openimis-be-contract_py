import graphene
from core import ExtendedConnection
from graphene_django import DjangoObjectType
from contract.models import Contract


class ContractGQLType(DjangoObjectType):

    class Meta:
        model = Contract
        exclude_fields = ('row_id',)
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            "uuid": ["exact"],
            "version": ["exact"],
            "amount_notified": ["exact", "lt", "lte", "gt", "gte"],
            "amount_rectified": ["exact", "lt", "lte", "gt", "gte"],
            "amount_due": ["exact", "lt", "lte", "gt", "gte"],

            "payment_due_date": ["exact", "lt", "lte", "gt", "gte"],
            "status": ["exact"],
            "payment_reference": ["exact", "istartswith", "icontains", "iexact"],

            "date_created": ["exact", "lt", "lte", "gt", "gte"],
            "date_updated": ["exact", "lt", "lte", "gt", "gte"],

            "contract_from": ["exact", "lt", "lte", "gt", "gte"],
            "contract_to": ["exact", "lt", "lte", "gt", "gte"]
        }

        connection_class = ExtendedConnection

    @classmethod
    def get_queryset(cls, queryset, info):
        return Contract.get_queryset(queryset, info)


