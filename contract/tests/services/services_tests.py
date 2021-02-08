import json

from unittest import TestCase
from contract.services import Contract as ContractService, ContractDetails as ContractDetailsService, \
    ContractContributionPlanDetails as ContractContributionPlanDetailsService
from contract.models import Contract, ContractDetails, ContractContributionPlanDetails
from policyholder.models import PolicyHolder, PolicyHolderInsuree
from policyholder.tests.helpers import create_test_policy_holder, create_test_policy_holder_insuree
from contribution.models import Premium
from contribution_plan.tests.helpers import create_test_contribution_plan, \
    create_test_contribution_plan_bundle, create_test_contribution_plan_bundle_details
from contribution_plan.models import ContributionPlan, ContributionPlanBundle, ContributionPlanBundleDetails
from policy.models import Policy
from policy.test_helpers import create_test_policy
from core.models import User
from payment.models import Payment, PaymentDetail


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
        for i in range(0, 5):
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
            "code": "CTSV",
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

    def test_contract_create_update_failed_ph(self):
        # create contract for contract with policy holder with two phinsuree
        policy_holder = create_test_policy_holder()
        policy_holder2 = create_test_policy_holder()

        # create contribution plan etc
        contribution_plan_bundle = create_test_contribution_plan_bundle()
        contribution_plan = create_test_contribution_plan()
        contribution_plan_bundle_details = create_test_contribution_plan_bundle_details(
            contribution_plan=contribution_plan, contribution_plan_bundle=contribution_plan_bundle
        )

        # create policy holder insuree
        for i in range(0, 1):
            create_test_policy_holder_insuree(policy_holder=policy_holder,
                                              contribution_plan_bundle=contribution_plan_bundle)

        contract = {
            "code": "CSTG",
            "policy_holder_id": str(policy_holder.id)
        }
        response = self.contract_service.create(contract)
        contract_id = str(response["data"]["id"])

        contract = {
            "id": contract_id,
            "policy_holder_id": str(policy_holder2.id),
        }
        response = self.contract_service.update(contract)
        failed = response['detail']

        # tear down the test data
        ContractDetails.objects.filter(contract_id=contract_id).delete()
        Contract.objects.filter(id=contract_id).delete()
        PolicyHolderInsuree.objects.filter(policy_holder_id=str(policy_holder.id)).delete()
        PolicyHolder.objects.filter(id=policy_holder.id).delete()
        PolicyHolder.objects.filter(id=policy_holder2.id).delete()
        ContributionPlanBundleDetails.objects.filter(id=contribution_plan_bundle_details.id).delete()
        ContributionPlanBundle.objects.filter(id=contribution_plan_bundle.id).delete()
        ContributionPlan.objects.filter(id=contribution_plan.id).delete()

        self.assertEqual(
            "ContractUpdateError: You cannot update already set PolicyHolder in Contract!", failed,
        )

    def test_contract_create_submit_fail_scenarios(self):
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
            "code": "MTD",
            "policy_holder_id": str(policy_holder.id)
        }
        response = self.contract_service.create(contract)
        contract_id = str(response["data"]["id"])

        contract_created = Contract.objects.filter(id=contract_id).first()
        contract_created.state = Contract.STATE_EXECUTABLE
        contract_created.save(username="admin")

        contract = {
            "id": contract_id,
        }

        response = self.contract_service.submit(contract)
        result_message = response["detail"]
        expected_message = "ContractUpdateError: The contract cannot be submitted because of current state!"

        contract_created.state = Contract.STATE_NEGOTIABLE
        contract_created.save(username="admin")

        response = self.contract_service.submit(contract)
        result_message2 = response["detail"]
        expected_message2 = "ContractUpdateError: The contract has been already submitted!"

        contract_created.policy_holder = None
        contract_created.save(username="admin")

        response = self.contract_service.submit(contract)
        result_message3 = response["detail"]
        expected_message3 = "ContractUpdateError: The contract does not contain PolicyHolder!"

        # tear down the test data
        list_cd = list(ContractDetails.objects.filter(contract_id=contract_id).values('id', 'json_ext'))
        ContractDetails.objects.filter(contract_id=contract_id).delete()
        Contract.objects.filter(id=contract_id).delete()
        PolicyHolderInsuree.objects.filter(policy_holder_id=str(policy_holder.id)).delete()
        PolicyHolder.objects.filter(id=policy_holder.id).delete()
        ContributionPlanBundleDetails.objects.filter(id=contribution_plan_bundle_details.id).delete()
        ContributionPlanBundle.objects.filter(id=contribution_plan_bundle.id).delete()
        ContributionPlan.objects.filter(id=contribution_plan.id).delete()

        self.assertEqual(
            (
                expected_message,
                expected_message2,
                expected_message3
            ),
            (
                result_message,
                result_message2,
                result_message3
            )
        )

    def test_contract_create_submit_counter(self):
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
            "code": "SUR",
            "policy_holder_id": str(policy_holder.id)
        }
        response = self.contract_service.create(contract)
        contract_id = str(response["data"]["id"])

        contract = {
            "id": contract_id,
        }
        self.contract_service.submit(contract)
        response = self.contract_service.counter(contract)
        result_state = response["data"]["state"]
        expected_state = 11

        # tear down the test data
        list_cd = list(ContractDetails.objects.filter(contract_id=contract_id).values('id', 'json_ext'))
        for cd in list_cd:
            ccpd = ContractContributionPlanDetails.objects.filter(contract_details__id=f"{cd['id']}").delete()
        ContractDetails.objects.filter(contract_id=contract_id).delete()
        Contract.objects.filter(id=contract_id).delete()
        PolicyHolderInsuree.objects.filter(policy_holder_id=str(policy_holder.id)).delete()
        PolicyHolder.objects.filter(id=policy_holder.id).delete()
        ContributionPlanBundleDetails.objects.filter(id=contribution_plan_bundle_details.id).delete()
        ContributionPlanBundle.objects.filter(id=contribution_plan_bundle.id).delete()
        ContributionPlan.objects.filter(id=contribution_plan.id).delete()

        self.assertEqual(
            expected_state, result_state
        )