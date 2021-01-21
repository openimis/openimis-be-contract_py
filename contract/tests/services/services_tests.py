from unittest import TestCase
from contract.services import Contract as ContractService, ContractDetails as ContractDetailsService, \
    ContractContributionPlanDetails as ContractContributionPlanDetailsService
from contract.models import Contract, ContractDetails, ContractContributionPlanDetails
from policyholder.models import PolicyHolder, PolicyHolderInsuree
from policyholder.tests.helpers import create_test_policy_holder, create_test_policy_holder_insuree
from contribution_plan.tests.helpers import create_test_contribution_plan, \
    create_test_contribution_plan_bundle, create_test_contribution_plan_bundle_details
from contribution_plan.models import ContributionPlan, ContributionPlanBundle, ContributionPlanBundleDetails
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
            'code': 'AAAAAA',
        }
        response = self.contract_service.create(contract)
        # tear down the test data
        Contract.objects.filter(id=response["data"]["id"]).delete()
        self.assertEqual(
            (
                 True,
                 "Ok",
                 "",
                 "AAAAAA",
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
        # tear down the test data
        ContractDetails.objects.filter(contract_id=response["data"]["id"]).delete()
        Contract.objects.filter(id=response["data"]["id"]).delete()
        PolicyHolderInsuree.objects.filter(policy_holder_id=str(policy_holder.id)).delete()
        PolicyHolder.objects.filter(id=policy_holder.id).delete()
        ContributionPlanBundleDetails.objects.filter(id=contribution_plan_bundle_details.id).delete()
        ContributionPlanBundle.objects.filter(id=contribution_plan_bundle.id).delete()
        ContributionPlan.objects.filter(id=contribution_plan.id).delete()
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

    def test_contract_create_update_delete_with_policy_holder(self):
        # create contract for contract with policy holder with two phinsuree
        policy_holder = create_test_policy_holder()

        # create contribution plan etc
        contribution_plan_bundle = create_test_contribution_plan_bundle()
        contribution_plan = create_test_contribution_plan()
        contribution_plan_bundle_details = create_test_contribution_plan_bundle_details(
            contribution_plan=contribution_plan, contribution_plan_bundle=contribution_plan_bundle
        )

        # create policy holder insuree
        for i in range(0, 3):
            create_test_policy_holder_insuree(policy_holder=policy_holder,
                                              contribution_plan_bundle=contribution_plan_bundle)

        contract = {
            "code": "CTS",
            "policy_holder_id": str(policy_holder.id)
        }
        response = self.contract_service.create(contract)
        contract_id = str(response["data"]["id"])
        expected_amount_notified = response["data"]["amount_notified"] + 400.50

        contract = {
            "id": contract_id,
            "amount_notified": expected_amount_notified,
        }
        response = self.contract_service.update(contract)
        updated_amount_notified = response['data']['amount_notified']

        contract = {
            "id": contract_id,
        }
        response = self.contract_service.delete(contract)
        is_deleted = response['success']

        # tear down the test data
        ContractDetails.objects.filter(contract_id=contract_id).delete()
        Contract.objects.filter(id=contract_id).delete()
        PolicyHolderInsuree.objects.filter(policy_holder_id=str(policy_holder.id)).delete()
        PolicyHolder.objects.filter(id=policy_holder.id).delete()
        ContributionPlanBundleDetails.objects.filter(id=contribution_plan_bundle_details.id).delete()
        ContributionPlanBundle.objects.filter(id=contribution_plan_bundle.id).delete()
        ContributionPlan.objects.filter(id=contribution_plan.id).delete()

        self.assertEqual(
            (expected_amount_notified, True),
            (updated_amount_notified, is_deleted)
        )