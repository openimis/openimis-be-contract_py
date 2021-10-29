import logging

from celery import shared_task
from core.models import User
from contract.services import Contract as ContractService


logger = logging.getLogger(__name__)


@shared_task
def approve_contracts(user_id, contracts):
    user = User.objects.get(id=user_id)
    contract_service = ContractService(user=user)
    for contract in contracts:
        output = contract_service.approve(contract={"id": contract})


@shared_task
def counter_contracts(user_id, contracts):
    user = User.objects.get(id=user_id)
    contract_service = ContractService(user=user)
    for contract in contracts:
        output = contract_service.counter(contract={"id": contract})