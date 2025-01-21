from calculation.services import run_calculation_rules
from core.signals import Signal
from django.conf import settings
from django.core.mail import BadHeaderError, send_mail
from django.db.models import Q, Subquery
from django.db.models.signals import post_save
from django.db import transaction
from django.dispatch import receiver
from insuree.apps import InsureeConfig
from insuree.models import InsureePolicy
from insuree.signals import signal_before_insuree_policy_query
from payment.apps import PaymentConfig
from payment.models import Payment, PaymentDetail
from payment.signals import signal_before_payment_query
from policy.signals import signal_check_formal_sector_for_policy
from policyholder.apps import PolicyholderConfig
from policyholder.models import PolicyHolderUser
import inspect
from .config import get_message_approved_contract
from .models import Contract, ContractContributionPlanDetails

_contract_signal_params = ["contract", "user"]
_contract_approve_signal_params = [
    "contract",
    "user",
    "contract_details_list",
    "service_object",
    "payment_service",
    "ccpd_service",
]
signal_contract = Signal(_contract_signal_params)
signal_contract_approve = Signal(_contract_signal_params)


def on_contract_signal(sender, **kwargs):
    contract = kwargs["contract"]
    user = kwargs["user"]
    __save_or_update_contract(contract=contract, user=user)
    return f"contract updated - state {contract.state}"


def on_contract_approve_signal(sender, instance, **kwargs):
    # approve scenario

    user = kwargs["user"]
    contract_service = kwargs["service_object"]
    payment_service = kwargs["payment_service"]
    ccpd_service = kwargs["ccpd_service"]
    # contract valuation
    contract_contribution_plan_details = contract_service.contract_valuation(
        instance, save=True
    )
    if not contract_contribution_plan_details["success"]:
        return contract_contribution_plan_details
    instance.amount_due = contract_contribution_plan_details["data"][
        "total_amount"
    ]
    contribution_result = ccpd_service.create_contribution(
        contract_contribution_plan_details["data"]
    )
    if not contribution_result.get('success', False):
        return contribution_result
    result_payment = __create_payment(
        instance, payment_service, contract_contribution_plan_details["data"]
    )
    if not result_payment.get('success', False):
        return result_payment
    # STATE_EXECUTABLE
    from core import datetime

    now = datetime.datetime.now()
    instance.date_approved = now
    instance.state = 5
    approved_contract = __save_or_update_contract(
        contract=instance, user=user
    )
    if instance.policy_holder.email:
        email_contact_name = (
            instance.policy_holder.contact_name["contactName"]
            if (
                instance.policy_holder.contact_name
                and "contactName" in instance.policy_holder.contact_name
            )
            else instance.policy_holder.trade_name
            or instance.policy_holder.code
        )
        __send_email_notify_payment(
            code=instance.code,
            name=instance.policy_holder.trade_name,
            contact_name=email_contact_name,
            amount_due=instance.amount_due,
            payment_reference=instance.payment_reference,
            email=instance.policy_holder.email,
        )
    return approved_contract


# additional filters for payment in 'contract' tab
def append_contract_filter(sender, **kwargs):
    user = kwargs.get("user", None)
    additional_filter = kwargs.get("additional_filter", None)
    if "contract" in additional_filter:
        # then check perms
        if user.has_perms(PaymentConfig.gql_query_payments_perms) or user.has_perms(
            PolicyholderConfig.gql_query_payment_portal_perms
        ):
            contract_id = additional_filter["contract"]
            contract_to_process = Contract.objects.filter(id=contract_id).first()

            if not contract_to_process or not contract_to_process.policy_holder:
                return Q(pk=-1)
            # check if user is linked to ph in policy holder user table
            type_user = f"{user}"
            # related to user object output (i) or (t)
            # check if we have interactive user from current context
            if "(i)" in type_user:
                from core import datetime

                now = datetime.datetime.now()

                ph_user = PolicyHolderUser.objects.filter(
                    Q(date_valid_to__isnull=True) | Q(date_valid_to__gte=now),
                    date_valid_from__lte=now,
                    policy_holder__id=contract_to_process.policy_holder.id,
                    user__id=user.id,
                ).first()

                if ph_user or user.has_perms(PaymentConfig.gql_query_payments_perms):
                    return Q(
                        **{
                            'payment_details__'
                            + 'premium__'
                            + 'contract_contribution_plan_details__'
                            + 'contract_details__contract__id': contract_id
                        }
                    )


# additional filters for InsureePolicy in contract
def append_contract_policy_insuree_filter(sender, **kwargs):
    user = kwargs.get("user", None)
    additional_filter = kwargs.get("additional_filter", None)
    if "contract" in additional_filter:
        # then check perms
        if user.has_perms(
            InsureeConfig.gql_query_insuree_policy_perms
        ) or user.has_perms(PolicyholderConfig.gql_query_insuree_policy_portal_perms):
            contract_id = additional_filter["contract"]
            contract_to_process = Contract.objects.filter(id=contract_id).first()
            if not contract_to_process or not contract_to_process.policy_holder:
                return Q(pk=-1)
            # check if user is linked to ph in policy holder user table
            type_user = f"{user}"
            # related to user object output (i) or (t)
            # check if we have interactive user from current context
            if "(i)" in type_user:
                from core import datetime

                now = datetime.datetime.now()
                ph_user = PolicyHolderUser.objects.filter(
                    Q(date_valid_to__isnull=True) | Q(date_valid_to__gte=now),
                    date_valid_from__lte=now,
                    policy_holder__id=contract_to_process.policy_holder.id,
                    user__id=user.id,
                ).first()

                if ph_user or user.has_perms(
                    InsureeConfig.gql_query_insuree_policy_perms
                ):
                    policies = list(
                        ContractContributionPlanDetails.objects.filter(
                            contract_details__contract__id=contract_id
                        ).values_list("policy", flat=True)
                    )

                    return Q(
                        start_date__gte=contract_to_process.date_valid_from,
                        start_date__lte=contract_to_process.date_valid_to,
                        policy__in=policies,
                    )


# check if policy is related to formal sector contract
def formal_sector_policies(sender, **kwargs):
    policy_id = kwargs.get("policy_id", None)
    ccpd = ContractContributionPlanDetails.objects.filter(
        policy__id=policy_id, is_deleted=False
    ).first()
    if ccpd:
        cd = ccpd.contract_details
        contract = cd.contract
        return contract.policy_holder
    else:
        return None


signal_contract.connect(on_contract_signal, dispatch_uid="on_contract_signal")
signal_contract_approve.connect(
    on_contract_approve_signal, dispatch_uid="on_contract_approve_signal"
)
signal_before_payment_query.connect(append_contract_filter)
signal_before_insuree_policy_query.connect(append_contract_policy_insuree_filter)
signal_check_formal_sector_for_policy.connect(formal_sector_policies)


@receiver(post_save, sender=Payment, dispatch_uid="payment_signal_paid")
def activate_contracted_policies(sender, instance, created,  **kwargs):
    received_amount = instance.received_amount if instance.received_amount else 0
    # check if payment is related to the contract
    if any(f.function == 'save_history' for f in inspect.stack()):
        return
    
    payment_detail = (
        PaymentDetail.objects.filter(payment=instance)
        .filter(premium__contract_contribution_plan_details__isnull=False)
        .prefetch_related(
            "premium__contract_contribution_plan_details__contract_details__contract"
        )
        .prefetch_related("premium__contract_contribution_plan_details")
        
    )
    if len(list(payment_detail)) > 0:
        if instance.expected_amount <= received_amount:
            contribution_list_id = list(set(pd.premium.id for pd in payment_detail))
            contract_list = Contract.objects.filter(
                contractdetails__contractcontributionplandetails__contribution__id__in=contribution_list_id
            ).distinct()
            ccpd_full_list = ContractContributionPlanDetails.objects.filter(
                contract_details__contract__in=Subquery(contract_list.values('id'))
            ).prefetch_related('contract_details')

            # 1- check if the contract have payment attached to each contributions
            # (nbr CCPD of all contract in step 0= Paymentdetails in Steps 0)
            if len(ccpd_full_list) == len(list(payment_detail)):
                for contract in contract_list:
                    if contract.state == Contract.STATE_EXECUTABLE:
                        # get the ccpd related to the currenttly processing contract
                        ccpd_list = [
                            ccpd for ccpd in ccpd_full_list if ccpd.contract_details.contract_id == contract.id
                        ]
                        # TODO support Splitted payment and check that
                        #  the payment match the value of all contributions
                        for ccpd in ccpd_list:
                            members = run_calculation_rules(
                                ccpd, "members", contract.user_updated
                            )
                            for insuree in members:
                                InsureePolicy.objects.create(
                                    **{
                                        "insuree": insuree,
                                        "policy": ccpd.policy,
                                        "enrollment_date": ccpd.date_valid_from,
                                        "start_date": ccpd.date_valid_from,
                                        "effective_date": ccpd.date_valid_from,
                                        "expiry_date": ccpd.date_valid_to,
                                        "audit_user_id": -1,
                                    }
                                )
                        contract.state = Contract.STATE_EFFECTIVE
                        __save_or_update_contract(contract, contract.user_updated)


def __save_json_external(user_id, datetime, message):
    return {
        "comments": [
            {"From": "Portal/webapp", "user": user_id, "date": datetime, "msg": message}
        ]
    }


def __save_or_update_contract(contract, user):
    contract.save(username=user.username)
    historical_record = contract.history.all().first()
    contract.json_ext = __save_json_external(
        user_id=str(historical_record.user_updated.id),
        datetime=str(historical_record.date_updated),
        message=f"contract updated - state " f"{historical_record.state}",
    )
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
    payment_details_data = payment_service.collect_payment_details(
        contract_cpd["contribution_plan_details"]
    )
    return payment_service.create(
        payment=payment_data, payment_details=payment_details_data
    )


def __send_email_notify_payment(
    code, name, contact_name, amount_due, payment_reference, email
):
    try:
        email = send_mail(
            subject="Contract payment notification",
            message=get_message_approved_contract(
                language=settings.LANGUAGE_CODE.split("-")[0],
                code=code,
                name=name,
                contact_name=contact_name,
                due_amount=amount_due,
                payment_reference=payment_reference,
            ),
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False,
        )
        return email
    except BadHeaderError:
        return ValueError("Invalid header found.")
