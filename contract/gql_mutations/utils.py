from contract.models import Contract


def update_or_create_contract(data, user):
    if "client_mutation_id" in data:
        data.pop('client_mutation_id')
    if "client_mutation_label" in data:
        data.pop('client_mutation_label')
    contract_uuid = data.pop('uuid') if 'uuid' in data else None
    if contract_uuid:
        contract = Contract.objects.get(uuid=contract_uuid)
        contract.save_history()
        [setattr(contract, key, data[key]) for key in data]
    else:
        contract = Contract.objects.create(**data)
    contract.save()
    return contract

