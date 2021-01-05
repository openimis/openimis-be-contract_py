import graphene

from core.schema import OpenIMISMutation, TinyInt


class ContractCreateInputType(OpenIMISMutation.Input):
    code = graphene.String(required=True, max_length=32)
    policy_holder_id = graphene.UUID(required=False)
    date_valid_from = graphene.Date(required=False)
    date_valid_to = graphene.Date(required=False)
    json_ext = graphene.types.json.JSONString(required=False)