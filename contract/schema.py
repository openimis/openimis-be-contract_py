import graphene
import graphene_django_optimizer as gql_optimizer

from django.db.models import Q
from core.schema import signal_mutation_module_before_mutating, OrderedDjangoFilterConnectionField
from core.utils import filter_validity_business_model
from contract.models import Contract, ContractDetails, \
    ContractContributionPlanDetails, ContractMutation
from contract.gql.gql_types import ContractGQLType, ContractDetailsGQLType, \
    ContractContributionPlanDetailsGQLType

from contract.gql.gql_mutations.contract_mutations import CreateContractMutation, \
    UpdateContractMutation, DeleteContractMutation, SubmitContractMutation, ApproveContractMutation, \
    ApproveContractBulkMutation, CounterContractMutation, AmendContractMutation
from contract.gql.gql_mutations.contract_details_mutations import CreateContractDetailsMutation, \
    UpdateContractDetailsMutation, DeleteContractDetailsMutation, \
    CreateContractDetailByPolicyHolderInsureeMutation
from contract.apps import ContractConfig


class Query(graphene.ObjectType):

    contract = OrderedDjangoFilterConnectionField(
        ContractGQLType,
        client_mutation_id=graphene.String(),
        insuree=graphene.UUID(),
        orderBy=graphene.List(of_type=graphene.String),
        dateValidFrom__Gte=graphene.DateTime(),
        dateValidTo__Lte=graphene.DateTime()
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

    def resolve_contract(self, info, **kwargs):
        if not info.context.user.has_perms(ContractConfig.gql_query_contract_perms):
           raise PermissionError("Unauthorized")

        filters = [*filter_validity_business_model(**kwargs)]
        client_mutation_id = kwargs.get("client_mutation_id", None)
        if client_mutation_id:
            filters.append(Q(mutations__mutation__client_mutation_id=client_mutation_id))

        insuree = kwargs.get('insuree', None)
        if insuree:
            filters.append(Q(contractdetails__insuree__uuid=insuree))

        return gql_optimizer.query(Contract.objects.filter(*filters).all(), info)

    def resolve_contract_details(self, info, **kwargs):
        if not info.context.user.has_perms(ContractConfig.gql_query_contract_perms):
           raise PermissionError("Unauthorized")

        filters = []
        client_mutation_id = kwargs.get("client_mutation_id", None)
        if client_mutation_id:
            filters.append(Q(mutations__mutation__client_mutation_id=client_mutation_id))

        return gql_optimizer.query(ContractDetails.objects.filter(*filters).all(), info)

    def resolve_contract_contribution_plan_details(self, info, **kwargs):
        if not info.context.user.has_perms(ContractConfig.gql_query_contract_perms):
           raise PermissionError("Unauthorized")

        query = ContractContributionPlanDetails.objects.all()

        insuree = kwargs.get('insuree', None)
        contribution_plan_bundle = kwargs.get('contributionPlanBundle', None)

        if insuree:
            query = query.filter(
                contract_details__insuree__uuid=insuree
            )

        if contribution_plan_bundle:
            query = query.filter(
                contributionplanbundledetails__contribution_plan_bundle__id=contribution_plan_bundle
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
    amend_contract = AmendContractMutation.Field()

    create_contract_details = CreateContractDetailsMutation.Field()
    update_contract_details = UpdateContractDetailsMutation.Field()
    delete_contract_details = DeleteContractDetailsMutation.Field()
    create_contract_details_by_ph_insuree = CreateContractDetailByPolicyHolderInsureeMutation.Field()


def on_contract_mutation(sender, **kwargs):
    uuids = kwargs['data'].get('uuids', [])
    if not uuids:
        uuid = kwargs['data'].get('uuid', None)
        uuids = [uuid] if uuid else []
    if not uuids:
        return []
    impacted_contracts = Contract.objects.filter(id__in=uuids).all()
    for contract in impacted_contracts:
        ContractMutation.objects.update_or_create(contract=contract, mutation_id=kwargs['mutation_log_id'])
    return []


signal_mutation_module_before_mutating["contract"].connect(on_contract_mutation)