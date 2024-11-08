import graphene
import graphene_django_optimizer as gql_optimizer
from core.gql_queries import ValidationMessageGQLType
from core.schema import (
    OrderedDjangoFilterConnectionField,
    signal_mutation_module_before_mutating,
)
from core.utils import append_validity_filter
from core.services import wait_for_mutation
from django.db.models import Q

from contract.apps import ContractConfig
from contract.gql.gql_mutations.contract_details_mutations import (
    CreateContractDetailByPolicyHolderInsureeMutation,
    CreateContractDetailsMutation,
    DeleteContractDetailsMutation,
    UpdateContractDetailsMutation,
)
from contract.gql.gql_mutations.contract_mutations import (
    AmendContractMutation,
    ApproveContractBulkMutation,
    ApproveContractMutation,
    ContractCreateInvoiceBulkMutation,
    CounterContractBulkMutation,
    CounterContractMutation,
    CreateContractMutation,
    DeleteContractMutation,
    RenewContractMutation,
    SubmitContractMutation,
    UpdateContractMutation,
)
from contract.gql.gql_types import (
    ContractContributionPlanDetailsGQLType,
    ContractDetailsGQLType,
    ContractGQLType,
)
from contract.models import (
    Contract,
    ContractContributionPlanDetails,
    ContractDetails,
    ContractMutation,
)
from contract.utils import filter_amount_contract

from .services import check_unique_code


class Query(graphene.ObjectType):

    contract = OrderedDjangoFilterConnectionField(
        ContractGQLType,
        client_mutation_id=graphene.String(),
        insuree=graphene.UUID(),
        orderBy=graphene.List(of_type=graphene.String),
        dateValidFrom__Gte=graphene.DateTime(),
        dateValidTo__Lte=graphene.DateTime(),
        amount_from=graphene.Decimal(),
        amount_to=graphene.Decimal(),
        applyDefaultValidityFilter=graphene.Boolean(),
    )

    contract_details = OrderedDjangoFilterConnectionField(
        ContractDetailsGQLType,
        client_mutation_id=graphene.String(),
        orderBy=graphene.List(of_type=graphene.String),
    )

    contract_contribution_plan_details = OrderedDjangoFilterConnectionField(
        ContractContributionPlanDetailsGQLType,
        insuree=graphene.UUID(),
        contributionPlanBundle=graphene.UUID(),
        orderBy=graphene.List(of_type=graphene.String),
    )

    validate_contract_code = graphene.Field(
        ValidationMessageGQLType,
        contract_code=graphene.String(required=True),
        description="Check that the specified contract code is unique.",
    )

    def resolve_validate_contract_code(self, info, **kwargs):
        if not info.context.user.has_perms(ContractConfig.gql_query_contract_perms):
            if not info.context.user.has_perms(
                ContractConfig.gql_query_contract_policyholder_portal_perms
            ):
                raise PermissionError("Unauthorized")
        errors = check_unique_code(code=kwargs["contract_code"])
        if errors:
            return ValidationMessageGQLType(False)
        else:
            return ValidationMessageGQLType(True)

    def resolve_contract(self, info, **kwargs):
        if not info.context.user.has_perms(ContractConfig.gql_query_contract_perms):
            if not info.context.user.has_perms(
                ContractConfig.gql_query_contract_policyholder_portal_perms
            ):
                raise PermissionError("Unauthorized")

        filters = append_validity_filter(**kwargs)
        client_mutation_id = kwargs.get("client_mutation_id", None)
        if client_mutation_id:
            wait_for_mutation(client_mutation_id)
            filters.append(
                Q(mutations__mutation__client_mutation_id=client_mutation_id)
            )

        insuree = kwargs.get("insuree", None)
        if insuree:
            filters.append(Q(contractdetails__insuree__uuid=insuree))

        # amount filters
        amount_from = kwargs.get("amount_from", None)
        amount_to = kwargs.get("amount_to", None)
        if amount_from or amount_to:
            filters.append(filter_amount_contract(**kwargs))
        return gql_optimizer.query(Contract.objects.filter(*filters).all(), info)

    def resolve_contract_details(self, info, **kwargs):
        if not info.context.user.has_perms(ContractConfig.gql_query_contract_perms):
            if not info.context.user.has_perms(
                ContractConfig.gql_query_contract_policyholder_portal_perms
            ):
                raise PermissionError("Unauthorized")

        filters = []
        client_mutation_id = kwargs.get("client_mutation_id", None)
        if client_mutation_id:
            wait_for_mutation(client_mutation_id)
            filters.append(
                Q(mutations__mutation__client_mutation_id=client_mutation_id)
            )

        return gql_optimizer.query(ContractDetails.objects.filter(*filters).all(), info)

    def resolve_contract_contribution_plan_details(self, info, **kwargs):
        if not info.context.user.has_perms(ContractConfig.gql_query_contract_perms):
            if not info.context.user.has_perms(
                ContractConfig.gql_query_contract_policyholder_portal_perms
            ):
                raise PermissionError("Unauthorized")

        query = ContractContributionPlanDetails.objects.all()

        insuree = kwargs.get("insuree", None)
        contribution_plan_bundle = kwargs.get("contributionPlanBundle", None)

        if insuree:
            query = query.filter(contract_details__insuree__uuid=insuree)

        if contribution_plan_bundle:
            query = query.filter(
                contract_details__contribution_plan_bundle__id=contribution_plan_bundle
            )

        return gql_optimizer.query(query.all(), info)


class Mutation(graphene.ObjectType):
    create_contract = CreateContractMutation.Field()
    update_contract = UpdateContractMutation.Field()
    delete_contract = DeleteContractMutation.Field()
    submit_contract = SubmitContractMutation.Field()
    approve_contract = ApproveContractMutation.Field()
    approve_bulk_contract = ApproveContractBulkMutation.Field()
    counter_contract = CounterContractMutation.Field()
    counter_bulk_contract = CounterContractBulkMutation.Field()
    amend_contract = AmendContractMutation.Field()
    renew_contract = RenewContractMutation.Field()
    create_contract_invoice_bulk = ContractCreateInvoiceBulkMutation.Field()

    create_contract_details = CreateContractDetailsMutation.Field()
    update_contract_details = UpdateContractDetailsMutation.Field()
    delete_contract_details = DeleteContractDetailsMutation.Field()
    create_contract_details_by_ph_insuree = (
        CreateContractDetailByPolicyHolderInsureeMutation.Field()
    )


def on_contract_mutation(sender, **kwargs):
    uuids = kwargs["data"].get("uuids", [])
    if not uuids:
        uuid = kwargs["data"].get("uuid", None)
        uuids = [uuid] if uuid else []
    if not uuids:
        return []
    impacted_contracts = Contract.objects.filter(id__in=uuids).all()
    for contract in impacted_contracts:
        ContractMutation.objects.update_or_create(
            contract=contract, mutation_id=kwargs["mutation_log_id"]
        )
    return []


signal_mutation_module_before_mutating["contract"].connect(on_contract_mutation)
