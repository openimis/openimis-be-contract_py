import graphene
from core.schema import OpenIMISMutation, TinyInt


class ContractInputType(OpenIMISMutation.Input):
    id = graphene.Int(required=False)
    version = graphene.Int(required=True)

    policy_holder = graphene.Int(required=True)

    amount_notified = graphene.Decimal(max_digits=18, decimal_places=2, required=True)
    amount_rectified = graphene.Decimal(max_digits=18, decimal_places=2, required=True)
    amount_due = graphene.Decimal(max_digits=18, decimal_places=2, required=True)

    payment_due_date = graphene.DateTime(required=False)
    status = TinyInt(required=True)
    payment_reference = graphene.String(required=True)

    json_ext = graphene.types.json.JSONString(required=False)

    date_created = graphene.DateTime(required=False)
    date_updated = graphene.DateTime(required=False)

    user_updated = graphene.Int(required=False)
    user_created = graphene.Int(required=False)

    contract_from = graphene.DateTime(required=False)
    contract_to = graphene.DateTime(required=False)


class ContractDetailsInputType(OpenIMISMutation.Input):
    id = graphene.Int(required=False)
    version = graphene.Int(required=True)

    contract_id = graphene.Int(required=True)
    policy_holder_insuree_id = graphene.Int(required=True)
    contribution_plan_bundle_id = graphene.Int(required=True)

    json_ext = graphene.types.json.JSONString(required=False)
    json_param = graphene.types.json.JSONString(required=False)
    json_param_history = graphene.types.json.JSONString(required=False)

    date_created = graphene.DateTime(required=False)
    date_updated = graphene.DateTime(required=False)

    user_updated = graphene.Int(required=False)
    user_created = graphene.Int(required=False)


class ContractContributionPlanDetailsInputType(OpenIMISMutation.Input):
    id = graphene.Int(required=False)
    version = graphene.Int(required=True)

    contribution_plan_id = graphene.Int(required=True)
    policy_id = graphene.Int(required=True)
    contract_details_id = graphene.Int(required=True)

    json_ext = graphene.Int(required=True)

    date_created = graphene.DateTime(required=False)
    date_updated = graphene.DateTime(required=False)

    user_updated = graphene.Int(required=False)
    user_created = graphene.Int(required=False)
