import json
import uuid

from .config import get_message_approved_contract
from .models import Contract, ContractDetails, ContractContributionPlanDetails
from core.signals import Signal
from django.db.models.signals import post_save
from django.core.serializers.json import DjangoJSONEncoder
from django.conf import settings
from django.core.mail import send_mail, BadHeaderError
from django.dispatch import receiver
from payment.models import Payment, PaymentDetail
from insuree.models import InsureePolicy


_contract_signal_params = ["contract", "user"]
_contract_approve_signal_params = ["contract", "user", "contract_details_list", "service_object", "payment_service", "ccpd_service"]
signal_contract = Signal(providing_args=_contract_signal_params)
signal_contract_approve = Signal(providing_args=_contract_signal_params)


def on_contract_signal(sender, **kwargs):
    contract = kwargs["contract"]
    user = kwargs["user"]
    __save_or_update_contract(contract=contract, user=user)
    return f"contract updated - state {contract.state}"


def on_contract_approve_signal(sender, **kwargs):
    # approve scenario
    user = kwargs["user"]
    contract_to_approve = kwargs["contract"]
    contract_details_list = kwargs["contract_details_list"]
    contract_service = kwargs["service_object"]
    payment_service = kwargs["payment_service"]
    ccpd_service = kwargs["ccpd_service"]
    # contract valuation
    contract_contribution_plan_details = contract_service.evaluate_contract_valuation(
        contract_details_result=contract_details_list,
        save=True
    )
    contract_to_approve.amount_due = contract_contribution_plan_details["total_amount"]
    result = ccpd_service.create_contribution(contract_contribution_plan_details)
    result_payment = __create_payment(contract_to_approve, payment_service, contract_contribution_plan_details)
    # STATE_EXECUTABLE
    from core import datetime
    now = datetime.datetime.now()
    contract_to_approve.date_approved = now
    contract_to_approve.state = 5
    approved_contract = __save_or_update_contract(contract=contract_to_approve, user=user)
    email = __send_email_notify_payment(
        code=contract_to_approve.code,
        name=contract_to_approve.policy_holder.trade_name,
        contact_name=contract_to_approve.policy_holder.contact_name,
        amount_due=contract_to_approve.amount_due,
        payment_reference=contract_to_approve.payment_reference,
        email=contract_to_approve.policy_holder.email,
    )
    return approved_contract


signal_contract.connect(on_contract_signal, dispatch_uid="on_contract_signal")
signal_contract_approve.connect(on_contract_approve_signal, dispatch_uid="on_contract_approve_signal")


@receiver(post_save, sender=Payment, dispatch_uid="payment_signal_paid")
def activate_contracted_policies(sender, instance, **kwargs):
    received_amount = instance.received_amount if instance.received_amount else 0
    # check if payment is related to the contract
    uuid_payment = instance.uuid
    if isinstance(uuid_payment, str):
        uuid_payment = str(uuid.UUID(uuid_payment))
    payment_detail = list(PaymentDetail.objects.filter(payment__id=int(instance.id)))
    contract = None
    if len(payment_detail) > 0:
        # for  fetching contract getting the first payment
        # detail from list would be enough to fetch it
        contract = ContractContributionPlanDetails.objects.filter(contribution_id=payment_detail[0].premium.id).first().contract_details.contract
    if contract:
        contribution_list_id = [pd.premium.id for pd in payment_detail]
        if instance.expected_amount <= received_amount and contract.state == Contract.STATE_EXECUTABLE:
            # get all contract contribution plan detail
            # get based on contribution
            # ccpd - contract contribution plan details
            ccpd_list = list(ContractContributionPlanDetails.objects.filter(contribution__id__in=contribution_list_id))
            contract_details = ContractDetails.objects.filter(contract__id=f'{contract.id}')
            from core import datetime, datetimedelta
            for ccpd in ccpd_list:
                insuree = ccpd.contract_details.insuree
                ip = InsureePolicy.objects.create(
                    **{
                        "insuree": insuree,
                        "policy": ccpd.policy,
                        "enrollment_date": ccpd.date_valid_from,
                        "start_date": ccpd.date_valid_from,
                        "effective_date": ccpd.date_valid_from,
                        "expiry_date": ccpd.date_valid_to + datetimedelta(
                            ccpd.contribution_plan.benefit_plan.grace_period
                        ),
                        "audit_user_id": -1,
                    }
                )
            contract.state = Contract.STATE_EFFECTIVE
            __save_or_update_contract(contract, contract.user_updated)


def __save_json_external(user_id, datetime, message):
    return {
        "comments": [{
            "From": "Portal/webapp",
            "user": user_id,
            "date": datetime,
            "msg": message
        }]
    }


def __save_or_update_contract(contract, user):
    contract.save(username=user.username)
    historical_record = contract.history.all().first()
    contract.json_ext = json.dumps(__save_json_external(
        user_id=historical_record.user_updated.id,
        datetime=historical_record.date_updated,
        message=f"contract updated - state "
                f"{historical_record.state}"
    ), cls=DjangoJSONEncoder)
    contract.save(username=user.username)
    return contract


def __create_payment(contract, payment_service, contract_cpd):
    from core import datetime
    now = datetime.datetime.now()
    # format payment data
    payment_data = {
        "expected_amount": contract.amount_due,
        "request_date": now,
    }
    payment_details_data = payment_service.collect_payment_details(contract_cpd["contribution_plan_details"])
    return payment_service.create(payment=payment_data, payment_details=payment_details_data)


def __send_email_notify_payment(code, name, contact_name, amount_due, payment_reference, email):
    try:
        email = send_mail(
            subject='Contract payment notification',
            message=get_message_approved_contract(
                language=settings.LANGUAGE_CODE.split('-')[0],
                code=code,
                name=name,
                contact_name=contact_name,
                due_amount=amount_due,
                payment_reference=payment_reference
            ),
            from_email= settings.EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False,
        )
        return email
    except BadHeaderError:
        return ValueError('Invalid header found.')