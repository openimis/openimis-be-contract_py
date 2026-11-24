from decimal import Decimal

from contribution.models import Premium
from contribution_plan.tests.helpers import (
    create_test_contribution_plan,
    create_test_contribution_plan_bundle,
    create_test_contribution_plan_bundle_details,
)
from core.models import User
from core.test_helpers import create_test_interactive_user
from django.db import connection
from django.test import TestCase
from policy.models import Policy
from policyholder.tests.helpers import (
    create_test_policy_holder,
    create_test_policy_holder_insuree,
)
from product.test_helpers import create_test_product

from contract.models import Contract, ContractContributionPlanDetails, ContractDetails
from contract.services import Contract as ContractService


class ContractLongerThanInsurancePeriodTest(TestCase):
    """
    A contract whose validity is longer than the product's insurance period is
    covered by several policies. Approving it must split the calculated amount
    over one ContractContributionPlanDetails row per policy, each with a positive
    premium, and the premiums must add up to the calculated amount.
    """

    income = 2000
    rate = 5
    expected_amount = Decimal("100")  # income * rate / 100
    date_from = "2026-10-01"
    date_to = "2027-10-19"

    @classmethod
    def setUpTestData(cls):
        print(f"\nTest DB: {connection.settings_dict['NAME']}")
        cls.user = User.objects.filter(username="Admin").first()
        if not cls.user:
            cls.user = create_test_interactive_user(username="Admin")
        cls.contract_service = ContractService(cls.user)

        cls.product = create_test_product(
            "CSPLIT", custom_props={"insurance_period": 12}
        )
        cls.contribution_plan = create_test_contribution_plan(
            product=cls.product,
            custom_props={
                "json_ext": {"calculation_rule": {"rate": cls.rate, "includeFamily": True}}
            },
        )
        cls.contribution_plan_bundle = create_test_contribution_plan_bundle()
        create_test_contribution_plan_bundle_details(
            contribution_plan=cls.contribution_plan,
            contribution_plan_bundle=cls.contribution_plan_bundle,
        )
        cls.policy_holder = create_test_policy_holder()
        cls.ph_insuree = create_test_policy_holder_insuree(
            policy_holder=cls.policy_holder,
            contribution_plan_bundle=cls.contribution_plan_bundle,
            custom_props={
                "last_policy": None,
                "json_ext": {"calculation_rule": {"income": cls.income}},
            },
        )

    def test_approve_contract_longer_than_insurance_period(self):
        response = self.contract_service.create({
            "code": "CSPLIT-2610",
            "policy_holder_id": str(self.policy_holder.id),
            "date_valid_from": self.date_from,
            "date_valid_to": self.date_to,
        })
        self.assertTrue(response["success"], response)
        contract_id = response["data"]["id"]

        response = self.contract_service.submit({"id": contract_id})
        self.assertTrue(response["success"], response)
        response = self.contract_service.approve({"id": contract_id})
        self.assertTrue(response["success"], response)

        contract = Contract.objects.get(id=contract_id)
        self.assertEqual(contract.state, Contract.STATE_EXECUTABLE, "contract not approved")

        insuree = self.ph_insuree.insuree
        details = list(ContractDetails.objects.filter(contract=contract, is_deleted=False))
        self.assertEqual(len(details), 1)
        ccpds = list(
            ContractContributionPlanDetails.objects.filter(
                contract_details__contract=contract, is_deleted=False
            ).order_by("date_valid_from")
        )
        policies = list(
            Policy.objects.filter(
                family=insuree.family,
                product=self.product,
                validity_to__isnull=True,
            ).order_by("start_date")
        )

        ccpd_summary = [
            (str(c.policy_id), str(c.date_valid_from), str(c.date_valid_to), c.amount,
             c.contribution.amount if c.contribution else None)
            for c in ccpds
        ]
        policy_summary = [(p.id, str(p.start_date), str(p.expiry_date)) for p in policies]
        print(f"Policies: {policy_summary}")
        print(f"CCPD (policy, from, to, amount, premium): {ccpd_summary}")

        # the contract spans more than one insurance period: two policies
        self.assertEqual(len(policies), 2, f"policies: {policy_summary}")

        # every Premium created for the contract is positive
        premiums = list(Premium.objects.filter(contract_contribution_plan_details__in=ccpds))
        self.assertTrue(premiums, "no premium created")
        for premium in premiums:
            self.assertGreater(
                premium.amount, 0,
                f"non-positive premium {premium.amount}; ccpd: {ccpd_summary}"
            )

        # the premiums of each contract detail add up to the calculated amount
        for detail in details:
            total = sum(
                c.contribution.amount for c in ccpds
                if c.contract_details_id == detail.id and c.contribution
            )
            self.assertEqual(
                Decimal(total), self.expected_amount,
                f"premium total {total} != {self.expected_amount}; ccpd: {ccpd_summary}"
            )

        # each policy gets its own ContractContributionPlanDetails row
        self.assertEqual(
            sorted(c.policy_id for c in ccpds),
            sorted(p.id for p in policies),
            f"ccpd per policy mismatch; policies: {policy_summary}; ccpd: {ccpd_summary}"
        )
