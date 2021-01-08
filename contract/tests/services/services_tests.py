from unittest import TestCase
from contract.services import Contract as ContractService, ContractDetails as ContractDetailsService, \
    ContractContributionPlanDetails as ContractContributionPlanDetailsService
from policyholder.models import PolicyHolder, PolicyHolderInsuree
from policyholder.tests.helpers import create_test_policy_holder, create_test_policy_holder_insuree
from contribution_plan.tests.helpers import create_test_contribution_plan, \
    create_test_contribution_plan_bundle, create_test_contribution_plan_bundle_details
from policy.models import Policy
from core.models import User


class ServiceTestPolicyHolder(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.get(username="admin")
        cls.contract_service = ContractService(cls.user)
        cls.contract_details_service = ContractDetailsService(cls.user)
        cls.contract_contribution_plan_details_service = ContractContributionPlanDetailsService(cls.user)

    def test_contract_create_without_policy_holder(self):
        contract = {
            'code': 'CONSERVICE2',
        }
        response = self.contract_service.create(contract)
        self.assertEqual(
            (
                 True,
                 "Ok",
                 "",
                 "CONSERVICE2",
                 0,
                 None,
            ),
            (
                 response['success'],
                 response['message'],
                 response['detail'],
                 response['data']['code'],
                 response['data']['amendment'],
                 response['data']['amount_notified'],
            )
        )

    def test_contract_create_with_policy_holder(self):
        # create policy holder for test
        policy_holder = create_test_policy_holder()

        # create contribution plan etc
        contribution_plan_bundle = create_test_contribution_plan_bundle()
        contribution_plan = create_test_contribution_plan()
        contribution_plan_bundle_details = create_test_contribution_plan_bundle_details(
            contribution_plan=contribution_plan, contribution_plan_bundle=contribution_plan_bundle)

        # create policy holder insuree
        for i in range(0,5):
            create_test_policy_holder_insuree(policy_holder=policy_holder, contribution_plan_bundle=contribution_plan_bundle)

        contract = {
            'code': 'CSCSD52',
            'policy_holder_id': policy_holder.id
        }
        response = self.contract_service.create(contract)
        self.assertEqual(
            (
                 True,
                 "Ok",
                 "",
                 "CSCSD52",
                 0,
            ),
            (
                 response['success'],
                 response['message'],
                 response['detail'],
                 response['data']['code'],
                 response['data']['amendment'],
            )
        )