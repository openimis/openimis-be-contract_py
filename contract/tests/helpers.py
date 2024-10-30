import datetime

from contribution.models import Premium
from contribution_plan.tests.helpers import (
    create_test_contribution_plan,
    create_test_contribution_plan_bundle,
)
from core.models import User
from insuree.test_helpers import create_test_insuree
from policy.test_helpers import create_test_policy
from policyholder.tests.helpers import create_test_policy_holder
from product.test_helpers import create_test_product

from contract.models import Contract, ContractContributionPlanDetails, ContractDetails


def create_test_contract(policy_holder=None, custom_props={}):
    if not policy_holder:
        policy_holder = create_test_policy_holder()

    user = __get_or_create_simple_contract_user()

    object_data = {
        "code": "CON",
        "policy_holder": policy_holder,
        "amount_notified": 0,
        "amount_rectified": 0,
        "amount_due": 0,
        "date_payment_due": datetime.date(2011, 10, 31),
        "state": 1,
        "payment_reference": "Payment Reference",
        "json_ext": {},
        **custom_props,
    }

    contract = Contract(**object_data)
    contract.save(username=user.username)

    return contract


def create_test_contract_details(
    contract=None, insuree=None, contribution_plan_bundle=None, custom_props={}
):
    if not contract:
        contract = create_test_contract()

    if not insuree:
        insuree = create_test_insuree()

    if not contribution_plan_bundle:
        contribution_plan_bundle = create_test_contribution_plan_bundle()

    user = __get_or_create_simple_contract_user()
    object_data = {
        "contract": contract,
        "insuree": insuree,
        "contribution_plan_bundle": contribution_plan_bundle,
        "json_param": {},
        **custom_props,
    }

    contract_details = ContractDetails(**object_data)
    contract_details.save(username=user.username)

    return contract_details


def create_test_contract_contribution_plan_details(
    contribution_plan=None,
    policy=None,
    contract_details=None,
    contribution=None,
    custom_props={},
):
    if not contribution_plan:
        contribution_plan = create_test_contribution_plan()

    if not policy:
        policy = create_test_policy(
            product=create_test_product(
                "TestCode",
                custom_props={
                    "insurance_period": 12,
                },
            ),
            insuree=create_test_insuree(),
        )

    if not contract_details:
        contract_details = create_test_contract_details()

    if not contribution:
        contribution = Premium.objects.create(
            **{
                "policy_id": policy.id,
                "payer_id": None,
                "amount": 1000,
                "receipt": "Test receipt",
                "pay_date": "2019-01-01",
                "validity_from": "2019-01-01",
                "audit_user_id": 1,
                "pay_type": "C",
            }
        )

    user = __get_or_create_simple_contract_user()
    object_data = {
        "contribution_plan": contribution_plan,
        "policy": policy,
        "contract_details": contract_details,
        "contribution": contribution,
        "json_ext": {},
        **custom_props,
    }

    contract_contribution_plan_details = ContractContributionPlanDetails(**object_data)
    contract_contribution_plan_details.save(username=user.username)

    return contract_contribution_plan_details


def __get_or_create_simple_contract_user():
    if not User.objects.filter(username="admin").exists():
        User.objects.create_superuser(username="admin", password="S/pe®Pąßw0rd™")
    user = User.objects.filter(username="admin").first()
    return user
