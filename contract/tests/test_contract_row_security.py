"""Contracts stay with the policy holders the user may see (audit C8, N01).

The back-office contract right reads the contracts of the policy holders in the
user's districts; the policy holder portal right reads only the contracts of the
policy holders the user is attached to.
"""

import json

from django.core.cache import cache
from django.test import override_settings

from contract.tests.helpers import (
    create_test_contract,
    create_test_contract_contribution_plan_details,
    create_test_contract_details,
)
from core.models.openimis_graphql_test_case import openIMISGraphQLTestCase, BaseTestContext
from core.test_helpers import create_right_only_user
from location.models import Location
from location.test_helpers import create_basic_test_locations
from policyholder.tests.helpers import create_test_policy_holder, create_test_policy_holder_user

CODES = {"C8-CON-A", "C8-CON-B"}
QUERIES = {
    "contract": "query { contract { edges { node { code } } } }",
    "contractDetails": "query { contractDetails { edges { node { contract { code } } } } }",
    "contractContributionPlanDetails":
        "query { contractContributionPlanDetails { edges { node {"
        " contractDetails { contract { code } } } } } }",
}


@override_settings(ROW_SECURITY=True)
class ContractRowSecurityTests(openIMISGraphQLTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_basic_test_locations()
        district_a = Location.objects.get(code="R1D1", validity_to__isnull=True)
        district_b = Location.objects.get(code="R2D1", validity_to__isnull=True)
        ph_a = create_test_policy_holder(custom_props={"code": "C8-PH-A", "locations": district_a})
        ph_b = create_test_policy_holder(custom_props={"code": "C8-PH-B", "locations": district_b})
        for ph, code in ((ph_a, "C8-CON-A"), (ph_b, "C8-CON-B")):
            contract = create_test_contract(policy_holder=ph, custom_props={"code": code})
            details = create_test_contract_details(contract=contract)
            create_test_contract_contribution_plan_details(contract_details=details)

        cls.staff_a = create_right_only_user("c8staffa", ["gql_query_contract_perms"], district_codes=["R1D1"])
        # A portal account has no district: what it sees comes from membership.
        cls.portal_a = create_right_only_user("c8portala", ["gql_query_contract_policyholder_portal_perms"])
        cls.no_right = create_right_only_user("c8noright", [], district_codes=["R1D1"])
        create_test_policy_holder_user(user=cls.portal_a, policy_holder=ph_a)
        cache.clear()

    def _gql(self, user, field):
        token = BaseTestContext(user=user).get_jwt()
        response = self.query(QUERIES[field], headers={"HTTP_AUTHORIZATION": f"Bearer {token}"})
        return json.loads(response.content)

    def _codes(self, user, field):
        content = self._gql(user, field)
        self.assertIsNone(content.get("errors"), field)
        codes = set()
        for edge in content["data"][field]["edges"]:
            node = edge["node"]
            node = node.get("contractDetails", node)
            node = node.get("contract", node)
            codes.add(node["code"])
        return codes & CODES

    def test_back_office_sees_own_districts(self):
        for field in QUERIES:
            self.assertEqual(self._codes(self.staff_a, field), {"C8-CON-A"}, field)

    def test_portal_user_sees_only_own_policy_holder(self):
        for field in QUERIES:
            self.assertEqual(self._codes(self.portal_a, field), {"C8-CON-A"}, field)

    def test_refused_without_right(self):
        for field in QUERIES:
            self.assertTrue(self._gql(self.no_right, field).get("errors"), field)
