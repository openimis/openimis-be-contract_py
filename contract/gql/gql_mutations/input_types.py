import graphene
from core.schema import OpenIMISMutation


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


class ContractUpdateInputType(OpenIMISMutation.Input):
    id = graphene.UUID(required=True)
    code = graphene.String(required=False, max_length=32)
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


class ContractSubmitInputType(OpenIMISMutation.Input):
    id = graphene.UUID(required=True)


class ContractApproveInputType(OpenIMISMutation.Input):
    id = graphene.UUID(required=True)


class ContractApproveBulkInputType(OpenIMISMutation.Input):
    contract_uuids = graphene.List(graphene.UUID, required=True)
    extended_filters = graphene.String(required=False)


class ContractCounterBulkInputType(OpenIMISMutation.Input):
    contract_uuids = graphene.List(graphene.UUID, required=True)
    extended_filters = graphene.String(required=False)


class ContractCounterInputType(OpenIMISMutation.Input):
    id = graphene.UUID(required=True)


class ContractCreateInvoiceBulkInputType(OpenIMISMutation.Input):
    contract_uuids = graphene.List(graphene.UUID, required=True)
    extended_filters = graphene.String(required=False)


class ContractAmendInputType(OpenIMISMutation.Input):
    id = graphene.UUID(required=True)
    amount_notified = graphene.Decimal(max_digits=18, decimal_places=2, required=False)
    amount_rectified = graphene.Decimal(max_digits=18, decimal_places=2, required=False)
    amount_due = graphene.Decimal(max_digits=18, decimal_places=2, required=False)
    date_approved = graphene.DateTime(required=False)
    date_payment_due = graphene.Date(required=False)
    payment_reference = graphene.String(required=False)
    date_valid_to = graphene.Date(required=False)
    json_ext = graphene.types.json.JSONString(required=False)


class ContractRenewInputType(OpenIMISMutation.Input):
    id = graphene.UUID(required=True)


class ContractDetailsCreateInputType(OpenIMISMutation.Input):
    id = graphene.UUID(required=False)
    contract_id = graphene.UUID(required=True)
    insuree_id = graphene.Int(required=True)
    contribution_plan_bundle_id = graphene.UUID(required=True)
    json_ext = graphene.types.json.JSONString(required=False)
    json_param = graphene.types.json.JSONString(required=False)


class ContractDetailsUpdateInputType(OpenIMISMutation.Input):
    id = graphene.UUID(required=True)
    contract_id = graphene.UUID(required=False)
    insuree_id = graphene.Int(required=False)
    contribution_plan_bundle_id = graphene.UUID(required=False)
    json_ext = graphene.types.json.JSONString(required=False)
    json_param = graphene.types.json.JSONString(required=False)


class ContractDetailsCreateFromInsureeInputType(OpenIMISMutation.Input):
    contract_id = graphene.UUID(required=True)
    policy_holder_insuree_id = graphene.UUID(required=True)
