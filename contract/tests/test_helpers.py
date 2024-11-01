from functools import lru_cache

from django.test import TestCase

from ..models import (
    ContractContributionPlanDetails,
    Contract,
    ContractDetails,
)
from .helpers import (
    create_test_contract_contribution_plan_details,
    create_test_contract_details,
    create_test_contract,
)
from insuree.test_helpers import (
    create_test_insuree,
)
from policyholder.tests.helpers import (
    create_test_policy_holder
)
from contribution_plan.tests.helpers import (
    create_test_contribution_plan_bundle
)
from contribution_plan.tests.helpers import create_test_contribution_plan


class HelpersTest(TestCase):
    """
    Class to check whether the helper methods responsible for creating test data work correctly.
    """

    def test_create_test_contract(self):
        contract = self.__create_test_contract()
        db_contract = Contract.objects.filter(id=contract.uuid).first()
        self.assertEqual(db_contract, contract, "Failed to create contract in helper")

    def test_create_test_contract_custom(self):
        contract = self.__create_test_contract(custom=True)
        db_contract = Contract.objects.filter(id=contract.uuid).first()
        params = self.__custom_contract_params
        self.assertEqual(db_contract.version, params["version"])
        self.assertEqual(db_contract.policy_holder, params["policy_holder"])
        self.assertEqual(db_contract.state, params["state"])

    def test_create_test_contract_details(self):
        contract_details = self.__create_test_contract_details()
        db_contract_details = ContractDetails.objects.filter(
            id=contract_details.uuid
        ).first()
        self.assertEqual(
            db_contract_details,
            contract_details,
            "Failed to create contract details in helper",
        )

    def test_create_test_contract_details_custom(self):
        contract_details = self.__create_test_contract_details(custom=True)
        db_contract_details = ContractDetails.objects.filter(
            id=contract_details.uuid
        ).first()
        params = self.__custom_contract_details_params

        self.assertEqual(db_contract_details.contract, params["contract"])
        self.assertEqual(db_contract_details.insuree, params["insuree"])
        self.assertEqual(
            db_contract_details.contribution_plan_bundle,
            params["contribution_plan_bundle"],
        )

    def test_create_test_contract_contribution_plan_details(self):
        contract_contribution_plan_details = (
            self.__create_test_contract_contribution_plan_details()
        )
        db_contract_contribution_plan_details = (
            ContractContributionPlanDetails.objects.filter(
                id=contract_contribution_plan_details.uuid
            ).first()
        )
        self.assertEqual(
            db_contract_contribution_plan_details,
            contract_contribution_plan_details,
            "Failed to create contract contribution plan details in helper",
        )

    def test_create_test_contract_contribution_plan_details_custom(self):
        contract_contribution_plan_details = (
            self.__create_test_contract_contribution_plan_details(custom=True)
        )
        db_contract_contribution_plan_details = (
            ContractContributionPlanDetails.objects.filter(
                id=contract_contribution_plan_details.uuid
            ).first()
        )
        params = self.__custom_contract_contribution_plan_details_params
        self.assertEqual(
            db_contract_contribution_plan_details.contribution_plan,
            params["contribution_plan"],
        )
        self.assertEqual(
            db_contract_contribution_plan_details.contract_details,
            params["contract_details"],
        )

    @property
    @lru_cache(maxsize=2)
    def __custom_contract_params(self):
        return {
            "version": 2,
            "policy_holder": create_test_policy_holder(custom_props={"version": 2}),
            "state": 1,
        }

    @property
    @lru_cache(maxsize=2)
    def __custom_contract_details_params(self):
        return {
            "contract": self.__create_test_contract(True),
            "contribution_plan_bundle": create_test_contribution_plan_bundle(
                custom_props={"version": 3}
            ),
            "insuree": create_test_insuree(),
        }

    @property
    @lru_cache(maxsize=2)
    def __custom_contract_contribution_plan_details_params(self):
        return {
            "contribution_plan": create_test_contribution_plan(
                custom_props={"version": 2}
            ),
            "contract_details": self.__create_test_contract_details(True),
        }

    def __create_test_instance(self, function, **kwargs):
        if kwargs:
            return function(**kwargs)
        else:
            return function()

    def __create_test_contract(self, custom=False):
        custom_params = self.__custom_contract_params if custom else {}
        return self.__create_test_instance(
            create_test_contract, custom_props=custom_params
        )

    def __create_test_contract_details(self, custom=False):
        custom_params = self.__custom_contract_details_params if custom else {}
        return self.__create_test_instance(
            create_test_contract_details, custom_props=custom_params
        )

    def __create_test_contract_contribution_plan_details(self, custom=False):
        custom_params = (
            self.__custom_contract_contribution_plan_details_params if custom else {}
        )
        return self.__create_test_instance(
            create_test_contract_contribution_plan_details, custom_props=custom_params
        )
