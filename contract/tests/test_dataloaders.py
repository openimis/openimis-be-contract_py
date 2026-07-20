from django.test import TestCase

from contract.dataloaders import (
    ContractDetailsByContractLoader,
    ContributionPlanDetailsByContractLoader,
)
from contract.models import ContractContributionPlanDetails, ContractDetails
from contract.tests.helpers import (
    create_test_contract,
    create_test_contract_contribution_plan_details,
    create_test_contract_details,
)


class ContractDetailsByContractLoaderTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.first_contract = create_test_contract()
        cls.second_contract = create_test_contract()
        cls.empty_contract = create_test_contract()

        cls.first_detail = create_test_contract_details(
            contract=cls.first_contract
        )
        cls.second_detail = create_test_contract_details(
            contract=cls.first_contract,
            insuree=cls.first_detail.insuree,
            contribution_plan_bundle=cls.first_detail.contribution_plan_bundle,
        )
        cls.other_contract_detail = create_test_contract_details(
            contract=cls.second_contract,
            insuree=cls.first_detail.insuree,
            contribution_plan_bundle=cls.first_detail.contribution_plan_bundle,
        )
        cls.deleted_detail = create_test_contract_details(
            contract=cls.first_contract,
            insuree=cls.first_detail.insuree,
            contribution_plan_bundle=cls.first_detail.contribution_plan_bundle,
        )
        ContractDetails.objects.filter(pk=cls.deleted_detail.pk).update(
            is_deleted=True
        )

    def test_batch_load_groups_results_in_key_order_and_excludes_deleted(self):
        contract_ids = [
            self.second_contract.id,
            self.empty_contract.id,
            self.first_contract.id,
        ]

        with self.assertNumQueries(1):
            results = ContractDetailsByContractLoader().batch_load_fn(
                contract_ids
            ).get()

        self.assertEqual(
            [[detail.id for detail in group] for group in results],
            [
                [self.other_contract_detail.id],
                [],
                sorted([self.first_detail.id, self.second_detail.id]),
            ],
        )

    def test_batch_load_selects_related_objects(self):
        with self.assertNumQueries(1):
            results = ContractDetailsByContractLoader().batch_load_fn(
                [self.first_contract.id]
            ).get()
            for detail in results[0]:
                detail.insuree
                detail.contribution_plan_bundle


class ContributionPlanDetailsLoaderTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.first_contract = create_test_contract()
        cls.second_contract = create_test_contract()
        cls.empty_contract = create_test_contract()

        cls.first_contract_detail = create_test_contract_details(
            contract=cls.first_contract
        )
        cls.second_contract_detail = create_test_contract_details(
            contract=cls.second_contract,
            insuree=cls.first_contract_detail.insuree,
            contribution_plan_bundle=(
                cls.first_contract_detail.contribution_plan_bundle
            ),
        )

        cls.first_row = create_test_contract_contribution_plan_details(
            contract_details=cls.first_contract_detail
        )
        shared_relations = {
            "contribution_plan": cls.first_row.contribution_plan,
            "policy": cls.first_row.policy,
            "contribution": cls.first_row.contribution,
        }
        cls.second_row = create_test_contract_contribution_plan_details(
            contract_details=cls.first_contract_detail,
            **shared_relations,
        )
        cls.other_contract_row = (
            create_test_contract_contribution_plan_details(
                contract_details=cls.second_contract_detail,
                **shared_relations,
            )
        )
        cls.deleted_row = create_test_contract_contribution_plan_details(
            contract_details=cls.first_contract_detail,
            **shared_relations,
        )
        ContractContributionPlanDetails.objects.filter(
            pk=cls.deleted_row.pk
        ).update(is_deleted=True)

    def test_batch_load_groups_results_in_key_order_and_excludes_deleted(self):
        contract_ids = [
            self.second_contract.id,
            self.empty_contract.id,
            self.first_contract.id,
        ]

        with self.assertNumQueries(1):
            results = ContributionPlanDetailsByContractLoader().batch_load_fn(
                contract_ids
            ).get()

        self.assertEqual(
            [[row.id for row in group] for group in results],
            [
                [self.other_contract_row.id],
                [],
                sorted([self.first_row.id, self.second_row.id]),
            ],
        )

    def test_batch_load_selects_related_objects(self):
        with self.assertNumQueries(1):
            results = ContributionPlanDetailsByContractLoader().batch_load_fn(
                [self.first_contract.id]
            ).get()
            for row in results[0]:
                row.contract_details
                row.contract_details.insuree
                row.contract_details.contribution_plan_bundle
                row.contribution_plan
                row.contribution
                row.policy
