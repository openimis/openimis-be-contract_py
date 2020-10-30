import json
import datetime

from contribution_plan.tests.helpers import create_test_contribution_plan_bundle, create_test_contribution_plan
from core.models import InteractiveUser, User
from insuree.test_helpers import create_test_insuree
from policy.test_helpers import create_test_policy
from product.test_helpers import create_test_product

from contract.models import Contract, ContractDetails, ContractContributionPlanDetails

from policyholder.tests.helpers import create_test_policy_holder, create_test_policy_holder_insuree


def create_test_contract(policy_holder=None, custom_props={}):
    if not policy_holder:
        policy_holder = create_test_policy_holder()
        policy_holder.save()
    pass

    user = __get_or_create_simple_contract_user()

    object_data = {
            'version': 1,
            'policy_holder': policy_holder,
            'amount_notified': 0,
            'amount_rectified': 0,
            'amount_due': 0,
            'payment_due_date': datetime.date(2011, 10, 31),
            'status': 1,
            'payment_reference': "Payment Reference",
            'json_ext': json.dumps("{}"),
            'date_created': datetime.date(2010, 10, 30),
            'date_updated': datetime.date(2010, 10, 31),
            'user_updated':  user,
            'user_created':  user,
            'contract_from': datetime.date(2010, 10, 30),
            'contract_to': None,
            **custom_props
    }
    return Contract.objects.create(**object_data)


def create_test_contract_details(contract=None, policy_holder_insuree=None,
                                 contribution_plan_bundle=None, custom_props={}):
    if not contract:
        contract = create_test_contract()

    if not policy_holder_insuree:
        policy_holder_insuree = create_test_policy_holder_insuree()

    if not contribution_plan_bundle:
        contribution_plan_bundle = create_test_contribution_plan_bundle()

    user = __get_or_create_simple_contract_user()
    object_data = {
        'contract': contract,
        'policy_holder_insuree': policy_holder_insuree,
        'contribution_plan_bundle': contribution_plan_bundle,
        'json_ext': json.dumps("{}"),
        'json_param': json.dumps("{}"),
        'json_param_history': json.dumps("{}"),
        'date_created': datetime.date(2010, 10, 30),
        'date_updated': datetime.date(2010, 10, 31),
        'user_updated': user,
        'user_created': user,
        **custom_props
    }
    return ContractDetails.objects.create(**object_data)


def create_test_contract_contribution_plan_details(contribution_plan=None, policy=None,
                                                          contract_details=None, custom_props={}):
    if not contribution_plan:
        contribution_plan = create_test_contribution_plan()

    if not policy:
        policy = create_test_policy(
            product=create_test_product("TestCode"),
            insuree=create_test_insuree())

    if not contract_details:
        contract_details = create_test_contract_details()

    user = __get_or_create_simple_contract_user()
    object_data = {
        'version': 1,
        'contribution_plan': contribution_plan,
        'policy':policy,
        'contract_details': contract_details,
        'json_ext': json.dumps("{}"),
        'date_created': datetime.date(2010, 10, 30),
        'date_updated': datetime.date(2010, 10, 31),
        'user_updated': user,
        'user_created': user,
        **custom_props
    }

    return ContractContributionPlanDetails.objects.create(**object_data)


def __get_or_create_simple_contract_user():
    user, _ = User.objects.get_or_create(username='contract_user',
                                         i_user=InteractiveUser.objects.first())
    return user