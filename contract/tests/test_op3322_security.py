"""Contract writes stay within the contracts the user may read (OP-3322).

The services, the bulk mutations and the contract line mutations used to look
their targets up with ``Contract.objects``, so a user could act on the contract
of a policy holder outside their districts by sending its id. The update also
copied every input field onto the contract, computed amounts included.
"""

import datetime

from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.test import TestCase, override_settings

from contract.gql.gql_mutations.contract_details_mutations import (
    CreateContractDetailsMutation,
)
from contract.gql.gql_mutations.contract_mutations import (
    ApproveContractBulkMutation,
    CounterContractBulkMutation,
)
from contract.gql.gql_mutations.mutations import (
    ContractDetailsFromPHInsureeMutationMixin,
    _scoped_contract_ids,
)
from contract.models import Contract, ContractDetails
from contract.services import Contract as ContractService
from contract.tests.helpers import create_test_contract
from contribution_plan.tests.helpers import create_test_contribution_plan_bundle
from core.test_helpers import create_right_only_user
from insuree.test_helpers import create_test_insuree
from location.models import Location
from location.test_helpers import create_basic_test_locations
from policyholder.tests.helpers import (
    create_test_policy_holder,
    create_test_policy_holder_insuree,
)

CONTRACT_PERMS = [
    "gql_query_contract_perms",
    "gql_mutation_create_contract_perms",
    "gql_mutation_update_contract_perms",
    "gql_mutation_approve_ask_for_change_contract_perms",
    "gql_mutation_delete_contract_perms",
    "gql_mutation_amend_contract_perms",
    "gql_mutation_renew_contract_perms",
    "gql_mutation_submit_contract_perms",
]


@override_settings(ROW_SECURITY=True)
class ContractScopedWritesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        create_basic_test_locations()
        district_a = Location.objects.get(code="R1D1", validity_to__isnull=True)
        district_b = Location.objects.get(code="R2D1", validity_to__isnull=True)
        cls.ph_a = create_test_policy_holder(
            custom_props={"code": "OP3322-PH-A", "locations": district_a}
        )
        cls.ph_b = create_test_policy_holder(
            custom_props={"code": "OP3322-PH-B", "locations": district_b}
        )
        cls.staff_a = create_right_only_user(
            "op3322ca", CONTRACT_PERMS, district_codes=["R1D1"]
        )
        cls.no_approve = create_right_only_user(
            "op3322cn", ["gql_query_contract_perms"], district_codes=["R1D1"]
        )
        cls.bundle = create_test_contribution_plan_bundle()
        cls.insuree_a = create_test_policy_holder_insuree(
            policy_holder=cls.ph_a, contribution_plan_bundle=cls.bundle
        ).insuree
        cls.insuree_b = create_test_policy_holder_insuree(
            policy_holder=cls.ph_b, contribution_plan_bundle=cls.bundle
        ).insuree

    def setUp(self):
        cache.clear()
        self.contract_a = self._contract(self.ph_a, "OP3322-CA")
        self.contract_b = self._contract(self.ph_b, "OP3322-CB")
        self.service = ContractService(self.staff_a)

    def _contract(self, policy_holder, code, state=Contract.STATE_DRAFT):
        today = datetime.date.today()
        return create_test_contract(
            policy_holder=policy_holder,
            custom_props={
                "code": code,
                "state": state,
                "date_valid_from": today,
                "date_valid_to": today + datetime.timedelta(days=30),
            },
        )

    def _assert_refused(self, result):
        self.assertFalse(result["success"])
        self.assertIn("No contract found", result["detail"])

    # Service lookups (#18)

    def test_update_out_of_scope_contract_is_refused(self):
        result = self.service.update(
            {"id": self.contract_b.id, "payment_reference": "changed"}
        )
        self._assert_refused(result)
        self.contract_b.refresh_from_db()
        self.assertEqual(self.contract_b.payment_reference, "Payment Reference")

    def test_update_in_scope_contract_still_works(self):
        result = self.service.update(
            {"id": self.contract_a.id, "payment_reference": "changed"}
        )
        self.assertTrue(result["success"], result)
        self.contract_a.refresh_from_db()
        self.assertEqual(self.contract_a.payment_reference, "changed")

    def test_state_changes_on_out_of_scope_contract_are_refused(self):
        negotiable = self._contract(self.ph_b, "OP3322-CBN", Contract.STATE_NEGOTIABLE)
        self._assert_refused(self.service.approve({"id": negotiable.id}))
        self._assert_refused(self.service.counter({"id": negotiable.id}))
        self._assert_refused(self.service.submit({"id": self.contract_b.id}))
        self._assert_refused(self.service.delete({"id": self.contract_b.id}))
        effective = self._contract(self.ph_b, "OP3322-CBE", Contract.STATE_EFFECTIVE)
        self._assert_refused(self.service.amend({"id": effective.id}))
        self._assert_refused(self.service.renew({"id": effective.id}))
        negotiable.refresh_from_db()
        self.assertEqual(negotiable.state, Contract.STATE_NEGOTIABLE)
        self.assertFalse(Contract.objects.get(id=self.contract_b.id).is_deleted)

    def test_create_with_out_of_scope_policy_holder_is_refused(self):
        result = self.service.create({
            "code": "OP3322-NEW",
            "policy_holder_id": self.ph_b.id,
            "date_valid_from": datetime.date.today(),
            "date_valid_to": datetime.date.today() + datetime.timedelta(days=30),
        })
        self.assertFalse(result["success"])
        self.assertFalse(Contract.objects.filter(code="OP3322-NEW").exists())

    def test_update_cannot_attach_out_of_scope_policy_holder(self):
        orphan = self._contract(self.ph_a, "OP3322-NOPH")
        Contract.objects.filter(id=orphan.id).update(policy_holder=None)
        result = self.service.update({"id": orphan.id, "policy_holder_id": self.ph_b.id})
        self.assertFalse(result["success"])
        orphan.refresh_from_db()
        self.assertIsNone(orphan.policy_holder_id)

    # Mass assignment (#18)

    def test_update_ignores_computed_fields(self):
        result = self.service.update({
            "id": self.contract_a.id,
            "payment_reference": "changed",
            "amount_notified": 1,
            "amount_rectified": 2,
            "amount_due": 3,
            "date_approved": datetime.datetime(2020, 1, 1),
            "amendment": 9,
        })
        self.assertTrue(result["success"], result)
        self.contract_a.refresh_from_db()
        self.assertEqual(self.contract_a.payment_reference, "changed")
        self.assertEqual(
            (
                self.contract_a.amount_notified,
                self.contract_a.amount_rectified,
                self.contract_a.amount_due,
                self.contract_a.date_approved,
                self.contract_a.amendment,
            ),
            (0, 0, 0, None, 0),
        )

    # Bulk mutations (#17)

    def test_bulk_approve_and_counter_require_the_right(self):
        for mutation in (ApproveContractBulkMutation, CounterContractBulkMutation):
            with self.assertRaises(PermissionDenied, msg=mutation.__name__):
                mutation.async_mutate(self.no_approve, contract_uuids=[self.contract_a.id])

    def test_bulk_ids_are_narrowed_to_the_user_scope(self):
        ids = [self.contract_a.id, self.contract_b.id]
        self.assertEqual(_scoped_contract_ids(self.staff_a, ids), [self.contract_a.id])
        queryset = Contract.objects.filter(id__in=ids)
        self.assertEqual(_scoped_contract_ids(self.staff_a, queryset), [self.contract_a.id])

    # Contract lines (#17)

    def _line(self, contract, insuree):
        return {
            "contract_id": contract.id,
            "insuree_id": insuree.id,
            "contribution_plan_bundle_id": self.bundle.id,
        }

    def test_contract_line_needs_an_in_scope_contract(self):
        with self.assertRaises(PermissionDenied):
            CreateContractDetailsMutation._validate_mutation(
                self.staff_a, **self._line(self.contract_b, self.insuree_b)
            )

    def test_contract_line_needs_an_insuree_of_the_policy_holder(self):
        with self.assertRaises(PermissionDenied):
            CreateContractDetailsMutation._validate_mutation(
                self.staff_a, **self._line(self.contract_a, self.insuree_b)
            )
        with self.assertRaises(PermissionDenied):
            CreateContractDetailsMutation._validate_mutation(
                self.staff_a, **self._line(self.contract_a, create_test_insuree())
            )
        # The insuree enrolled with the contract's policy holder is accepted.
        CreateContractDetailsMutation._validate_mutation(
            self.staff_a, **self._line(self.contract_a, self.insuree_a)
        )

    # Contract lines from a policy holder insuree (#18 bug)

    def test_line_from_ph_insuree_adds_only_that_insuree(self):
        other = create_test_policy_holder_insuree(
            policy_holder=self.ph_a, contribution_plan_bundle=self.bundle
        )
        phi = create_test_policy_holder_insuree(
            policy_holder=self.ph_a, contribution_plan_bundle=self.bundle
        )
        result = ContractDetailsFromPHInsureeMutationMixin.create_cd_from_ph_insuree(
            self.staff_a,
            {"contract_id": self.contract_a.id, "policy_holder_insuree_id": phi.id},
        )
        self.assertTrue(result["success"], result)
        lines = ContractDetails.objects.filter(contract=self.contract_a)
        self.assertEqual([line.insuree_id for line in lines], [phi.insuree_id])
        self.assertNotEqual(other.insuree_id, phi.insuree_id)

    def test_line_from_ph_insuree_refuses_out_of_scope_contract(self):
        phi = create_test_policy_holder_insuree(
            policy_holder=self.ph_b, contribution_plan_bundle=self.bundle
        )
        result = ContractDetailsFromPHInsureeMutationMixin.create_cd_from_ph_insuree(
            self.staff_a,
            {"contract_id": self.contract_b.id, "policy_holder_insuree_id": phi.id},
        )
        self.assertFalse(result["success"])
        self.assertFalse(ContractDetails.objects.filter(contract=self.contract_b).exists())
