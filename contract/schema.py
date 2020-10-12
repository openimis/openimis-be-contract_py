import graphene_django_optimizer as gql_optimizer

from contract.gql_queries import ContractGQLType
from contract.models import ContractMutation, Contract
from core.schema import OrderedDjangoFilterConnectionField
from core.schema import signal_mutation_module_validate
from contract.gql_mutations import *


class Query(graphene.ObjectType):
    contract = OrderedDjangoFilterConnectionField(ContractGQLType)

    def resolve_contract(self, info, **kwargs):
        query = Contract.objects
        return gql_optimizer.query(query.all(), info)


class Mutation(graphene.ObjectType):
    create_contract = CreateContractMutation.Field()
    update_contract = UpdateContractMutation.Field()
    delete_contract = DeleteContractMutation.Field()
    submit_contract = SubmitContractMutation.Field()
    

def on_contract_mutation(sender, **kwargs):
    uuids = kwargs['data'].get('uuids', [])
    if not uuids:
        uuid = kwargs['data'].get('contract_uuid', None)
        uuids = [uuid] if uuid else []
    if not uuids:
        return []
    impacted_contracts = Contract.objects.filter(uuid__in=uuids).all()
    for contract in impacted_contracts:
        ContractMutation.objects.create(
            contract=contract, mutation_id=kwargs['mutation_log_id'])
    return []


def bind_signals():
    signal_mutation_module_validate["contract"].connect(on_contract_mutation)



