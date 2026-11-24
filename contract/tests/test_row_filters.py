"""get_queryset honours the OP-2029 validity contract (epic OP-3317, phase 1).

Explicit validity values return the expected rows; a caller asking for
nothing gets what it got before the contract existed.
"""

from django.test import TestCase

from core.models.row_filters import Audits
from core.test_helpers import assert_row_filters, create_test_interactive_user, mark_deleted
from contract.models import Contract
from contract.tests.helpers import create_test_contract


class ContractRowFiltersTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_test_interactive_user(username="contractrowfilters")

    def test_contract(self):
        live = create_test_contract(custom_props={"code": "RWF1"}, user=self.user)
        deleted = mark_deleted(create_test_contract(custom_props={"code": "RWF2"}, user=self.user))
        assert_row_filters(
            self, Contract, Contract.objects.filter(id__in=[live.id, deleted.id]), self.user,
            live.id, deleted.id, default_hides_deleted=True,
        )

    def test_audits_come_from_the_history_table(self):
        contract = create_test_contract(custom_props={"code": "RWF3"}, user=self.user)
        contract.payment_reference = "changed"
        contract.save(username=self.user.username)
        trail = Contract.get_audit_queryset(self.user, audits=Audits.ALL).filter(id=contract.id)
        self.assertEqual({"Payment Reference", "changed"}, set(trail.values_list("payment_reference", flat=True)))
        with self.assertRaises(ValueError):
            Contract.get_queryset(Contract.objects.filter(id=contract.id), self.user, audits=Audits.ALL)
