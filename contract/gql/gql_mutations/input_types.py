import graphene

from core.schema import OpenIMISMutation, TinyInt


class ContractCreateInputType(OpenIMISMutation.Input):
    code = graphene.String(required=True, max_length=32)
    policy_holder_id = graphene.UUID(required=False)

    amount_notified = graphene.Decimal(max_digits=18, decimal_places=2, required=False)
    amount_rectified = graphene.Decimal(max_digits=18, decimal_places=2, required=False)
    amount_due = graphene.Decimal(max_digits=18, decimal_places=2, required=False)

    date_approved = graphene.DateTime(required=False)
    date_payment_due = graphene.Date(required=False)

    payment_reference = graphene.String(required=False)
    amendment = graphene.Int(required=False)

    date_valid_from = graphene.Date(required=False)
    date_valid_to = graphene.Date(required=False)
    json_ext = graphene.types.json.JSONString(required=False)