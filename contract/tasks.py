import logging

from celery import shared_task
from core.models import User
from contract.models import Contract, ContractContributionPlanDetails
from contract.services import Contract as ContractService, ContractToInvoiceService


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


@shared_task
def create_invoice_from_contracts(user_id, contracts):
    user = User.objects.get(id=user_id)
    contract_service = ContractToInvoiceService(user=user)
    for contract in contracts:
        contract_instance = Contract.objects.filter(id=contract)
        if contract_instance:
            contract_instance = contract_instance.first()
            ccpd_list = ContractContributionPlanDetails.objects.filter(contract_details__contract=contract_instance)
            output = contract_service.create_invoice(
                instance=contract_instance,
                convert_to="InvoiceLine",
                user=user,
                ccpd_list=ccpd_list
            )
