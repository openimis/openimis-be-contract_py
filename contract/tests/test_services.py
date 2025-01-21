import datetime

from calculation.services import (
    get_linked_class,
    get_parameters,
    get_rule_details,
    get_rule_name,
)
from contribution_plan.tests.helpers import (
    create_test_contribution_plan,
    create_test_contribution_plan_bundle,
    create_test_contribution_plan_bundle_details,
)
from core.models import User
from core.test_helpers import create_test_interactive_user
from django.test import TestCase
from policy.test_helpers import create_test_policy
from policyholder.tests.helpers import (
    create_test_policy_holder,
    create_test_policy_holder_insuree,
)

from contract.models import Contract, ContractContributionPlanDetails, ContractDetails
from contract.services import Contract as ContractService
from contract.services import (
    ContractContributionPlanDetails as ContractContributionPlanDetailsService,
)
from contract.services import ContractDetails as ContractDetailsService
from contract.services import subtract_date_ranges


class ServiceTestContract(TestCase):
    user = None

    @classmethod
    def setUpClass(cls):
        super(ServiceTestContract, cls).setUpClass()
        cls.user = User.objects.filter(username="admin").first()
        if not cls.user:
            cls.user = create_test_interactive_user(
                username="admin", password="S/pe®Pąßw0rd™"
            )
        cls.contract_service = ContractService(cls.user)
        cls.contract_details_service = ContractDetailsService(cls.user)
        cls.contract_contribution_plan_details_service = (
            ContractContributionPlanDetailsService(cls.user)
        )
        # some test data so as to created contract properly
        cls.income = 500
        cls.rate = 5
        cls.number_of_insuree = 5
        cls.policy_holder = create_test_policy_holder()
        cls.policy_holder2 = create_test_policy_holder()
        cls.time_stamp = datetime.datetime.now()
        cls.date_from = str((cls.time_stamp + datetime.timedelta(days=30)).date())
        cls.date_to = str((cls.time_stamp + datetime.timedelta(days=60)).date())
        # create contribution plans etc
        cls.contribution_plan_bundle = create_test_contribution_plan_bundle()
        cls.contribution_plan = create_test_contribution_plan(
            custom_props={"json_ext": {"calculation_rule": {"rate": cls.rate, 'includeFamily': True}}}
        )
        cls.contribution_plan_bundle_details = (
            create_test_contribution_plan_bundle_details(
                contribution_plan=cls.contribution_plan,
                contribution_plan_bundle=cls.contribution_plan_bundle,
            )
        )
        # create policy holder insuree for that test policy holder
        for i in range(0, cls.number_of_insuree):
            ph_insuree = create_test_policy_holder_insuree(
                policy_holder=cls.policy_holder,
                contribution_plan_bundle=cls.contribution_plan_bundle,
                custom_props={
                    "last_policy": None,
                    "json_ext": {"calculation_rule": {"income": cls.income}},
                },
            )
            create_test_policy(
                cls.contribution_plan.benefit_plan,
                ph_insuree.insuree,
                custom_props={
                    "start_date": datetime.datetime(2016, 3, 1),
                    "expiry_date": datetime.datetime(2021, 7, 1),
                },
            )

    def test_contract_create_without_policy_holder(self):
        contract = {
            "code": "AAAAAA",
            "date_valid_from": self.date_from,
            "date_valid_to": self.date_to,
        }
        response = self.contract_service.create(contract)
        # tear down the test data
        # Contract.objects.filter(id=response["data"]["id"]).delete()
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
                response["success"],
                response["message"],
                response["detail"],
                response["data"]["code"],
                response["data"]["amendment"],
                response["data"]["amount_notified"],
            ),
        )

    def test_contract_create_with_policy_holder(self):
        contract = {
            "code": "TESTONE",
            "policy_holder_id": self.policy_holder.id,
            "date_valid_from": self.date_from,
            "date_valid_to": self.date_to,
        }
        response = self.contract_service.create(contract)
        # tear down the test data
        # ContractDetails.objects.filter(contract_id=response["data"]["id"]).delete()
        # Contract.objects.filter(id=response["data"]["id"]).delete()
        self.assertEqual(
            (
                True,
                "Ok",
                "",
                "TESTONE",
                0,
            ),
            (
                response["success"],
                response["message"],
                response["detail"],
                response["data"]["code"],
                response["data"]["amendment"],
            ),
        )

    def test_contract_create_update_delete_with_policy_holder(self):
        contract = {
            "code": "CTSV",
            "policy_holder_id": self.policy_holder.id,
            "date_valid_from": self.date_from,
            "date_valid_to": self.date_to,
        }
        response = self.contract_service.create(contract)
        contract_id = str(response["data"]["id"])

        contract = {
            "id": contract_id,
            "payment_reference": "payment_one xxxxxxxx",
            "date_valid_from": self.date_from,
            "date_valid_to": self.date_to,
        }
        response = self.contract_service.update(contract)
        updated_payment_reference = response["data"]["payment_reference"]

        contract = {
            "id": contract_id,
        }
        response = self.contract_service.delete(contract)
        is_deleted = response["success"]

        # tear down the test data
        # ContractDetails.objects.filter(contract_id=contract_id).delete()
        # Contract.objects.filter(id=contract_id).delete()

        self.assertEqual(
            ("payment_one xxxxxxxx", True), (updated_payment_reference, is_deleted)
        )

    def test_contract_create_update_failed_ph(self):
        contract = {
            "code": "CSTG",
            "policy_holder_id": self.policy_holder.id,
            "date_valid_from": self.date_from,
            "date_valid_to": self.date_to,
        }

        response = self.contract_service.create(contract)
        contract_id = str(response["data"]["id"])

        contract = {
            "id": contract_id,
            "policy_holder_id": str(self.policy_holder2.id),
        }
        response = self.contract_service.update(contract)
        failed = response["detail"]

        # tear down the test data
        # ContractDetails.objects.filter(contract_id=contract_id).delete()
        # Contract.objects.filter(id=contract_id).delete()

        self.assertEqual(
            "ContractUpdateError: You cannot update already set PolicyHolder in Contract!",
            failed,
        )

    def test_contract_create_submit_fail_scenarios(self):
        contract = {
            "code": "MTD",
            "policy_holder_id": self.policy_holder.id,
            "date_valid_from": self.date_from,
            "date_valid_to": self.date_to,
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
        expected_message2 = (
            "ContractUpdateError: The contract has been already submitted!"
        )

        contract_created.policy_holder = None
        contract_created.save(username="admin")

        response = self.contract_service.submit(contract)
        result_message3 = response["detail"]
        expected_message3 = (
            "ContractUpdateError: The contract does not contain PolicyHolder!"
        )

        # tear down the test data
        list_cd = list(
            ContractDetails.objects.filter(contract_id=contract_id).values(
                "id", "json_ext"
            )
        )
        self.assertNotEqual(list_cd, [])
        # ContractDetails.objects.filter(contract_id=contract_id).delete()
        # Contract.objects.filter(id=contract_id).delete()

        self.assertEqual(
            (expected_message, expected_message2, expected_message3),
            (result_message, result_message2, result_message3),
        )

    def test_contract_create_submit_counter(self):
        contract = {
            "code": "SUR",
            "policy_holder_id": str(self.policy_holder.id),
            "date_valid_from": self.date_from,
            "date_valid_to": self.date_to,
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
        list_cd = list(
            ContractDetails.objects.filter(contract_id=contract_id).values("id")
        )
        self.assertNotEqual(list_cd, [])
        # for cd in list_cd:
        #    ccpd = ContractContributionPlanDetails.objects.filter(contract_details__id=f"{cd['id']}").delete()
        # ContractDetails.objects.filter(contract_id=contract_id).delete()
        # Contract.objects.filter(id=contract_id).delete()

        self.assertEqual(expected_state, result_state)

    def test_contract_create_submit(self):

        contract = {
            "code": "TESTCON",
            "policy_holder_id": str(self.policy_holder.id),
            "date_valid_from": self.date_from,
            "date_valid_to": self.date_to,
        }
        response = self.contract_service.create(contract)
        contract_id = str(response["data"]["id"])
        contract = {
            "id": contract_id,
        }
        response = self.contract_service.submit(contract)
        expected_state = 4
        result_state = response["data"]["state"]
        # tear down the test data
        list_cd = list(
            ContractDetails.objects.filter(contract_id=contract_id).values("id")
        )
        for cd in list_cd:
            ContractContributionPlanDetails.objects.filter(
                contract_details__id=f"{cd['id']}"
            ).delete()
        # ContractDetails.objects.filter(contract_id=contract_id).delete()
        # Contract.objects.filter(id=contract_id).delete()
        self.assertEqual(expected_state, result_state)

    def test_contract_create_cd_from_phi(self):

        ph_insuree2 = create_test_policy_holder_insuree(
            policy_holder=self.policy_holder,
            contribution_plan_bundle=self.contribution_plan_bundle,
            custom_props={
                "last_policy": None,
                "json_ext": {"calculation_rule": {"income": 400}},
            },
        )
        contract = {
            "code": "MTEST-1",
            "policy_holder_id": str(self.policy_holder.id),
            "date_valid_from": self.date_from,
            "date_valid_to": self.date_to,
        }
        response = self.contract_service.create(contract)
        contract_id = str(response["data"]["id"])
        contract = Contract.objects.get(id=contract_id)

        response = self.contract_details_service.get_details_from_ph_insuree(
            contract=contract, ph_insuree=ph_insuree2.id
        )
        # tear down the test data
        # ContractDetails.objects.filter(contract_id=contract_id).delete()
        # Contract.objects.filter(id=contract_id).delete()

        self.assertEqual(True, response["success"])

    def test_date_subtract(self):
        date_range = (
            datetime.date(2024, 1, 1),
            datetime.date(2024, 12, 31),
        )
        date_ranges = [
            (datetime.date(2024, 2, 1), datetime.date(2024, 3, 15)),
            (datetime.date(2024, 5, 1), datetime.date(2024, 6, 30)),
            (datetime.date(2024, 8, 1), datetime.date(2024, 9, 30)),
        ]

        result = subtract_date_ranges(date_range, date_ranges)

        per_1 = (datetime.date(2024, 1, 1), datetime.date(2024, 2, 1))
        per_2 = (datetime.date(2024, 3, 15), datetime.date(2024, 5, 1))
        per_3 = (datetime.date(2024, 6, 30), datetime.date(2024, 8, 1))
        per_4 = (datetime.date(2024, 9, 30), datetime.date(2024, 12, 31))

        self.assertTrue(per_1 in result)
        self.assertTrue(per_2 in result)
        self.assertTrue(per_3 in result)
        self.assertTrue(per_4 in result)


class CalculationContractTest(TestCase):
    user = None

    @classmethod
    def setUpClass(cls):
        super(CalculationContractTest, cls).setUpClass()
        cls.user = User.objects.filter(username="admin").first()
        if not cls.user:
            cls.user = create_test_interactive_user(
                username="admin", password="S/pe®Pąßw0rd™"
            )
        cls.contract_service = ContractService(cls.user)
        cls.income = 500
        cls.rate = 5
        cls.number_of_insuree = 5
        cls.policy_holder = create_test_policy_holder()
        cls.time_stamp = datetime.datetime.now()
        cls.date_from = str((cls.time_stamp + datetime.timedelta(days=30)).date())
        cls.date_to = str((cls.time_stamp + datetime.timedelta(days=60)).date())
        # create contribution plans etc
        cls.contribution_plan_bundle = create_test_contribution_plan_bundle()
        cls.contribution_plan = create_test_contribution_plan(
            custom_props={"json_ext": {"calculation_rule": {"rate": cls.rate}}}
        )
        cls.contribution_plan_bundle_details = (
            create_test_contribution_plan_bundle_details(
                contribution_plan=cls.contribution_plan,
                contribution_plan_bundle=cls.contribution_plan_bundle,
            )
        )

        # create policy holder insuree for that test policy holder
        for i in range(0, cls.number_of_insuree):
            create_test_policy_holder_insuree(
                policy_holder=cls.policy_holder,
                contribution_plan_bundle=cls.contribution_plan_bundle,
                custom_props={
                    "last_policy": None,
                    "json_ext": {"calculation_rule": {"income": cls.income}},
                },
            )

    def test_get_rule_name(self):
        class_name = "ContractDetails"
        result = get_rule_name(class_name=class_name)
        self.assertEqual("ContributionValuationRule", result[0].__name__)

    def test_get_rule_not_existing(self):
        class_name = "xxxxxxxxxxxxxxxxxxx"
        result = get_rule_name(class_name=class_name)
        self.assertEqual([], result)

    def test_get_rule_details(self):
        class_name = "PolicyHolderInsuree"
        class_name2 = "ContributionPlan"
        result = get_rule_details(class_name=class_name)
        result2 = get_rule_details(class_name=class_name2)
        result_param = [param["name"] for param in result[class_name]]
        result2_param = [param["name"] for param in result2[class_name2]]
        self.assertEqual(
            (class_name, class_name2, ["income"], ["rate", "includeFamily"]),
            (
                list(result.keys())[0],
                list(result2.keys())[0],
                result_param,
                result2_param,
            ),
        )

    def test_get_rule_details_not_existing(self):
        class_name = "xxxxxxxxxxxxxxx"
        result = get_rule_details(class_name=class_name)
        self.assertEqual({}, result)

    def test_get_linked_class_empty(self):
        result = get_linked_class()
        self.assertEqual(["Calculation"], result)

    def test_get_linked_class(self):
        result = get_linked_class(["PolicyHolderInsuree"])
        self.assertEqual(
            sorted(
                [
                    "PolicyHolder",
                    "Insuree",
                    "ContributionPlanBundle",
                    "Policy",
                    "Calculation",
                ]
            ),
            sorted(result),
        )

    def test_get_param_and_amount_calculation(self):
        # create contract to test 1st calculation rule contribution valuation
        # test case - create contract and check if amount is calcutated properly
        # and test if on instance of contract details the proper params is showed
        # by getting param name
        contract = {
            "code": "CALTEST",
            "policy_holder_id": self.policy_holder.id,
            "date_valid_from": self.date_from,
            "date_valid_to": self.date_to,
        }

        response = self.contract_service.create(contract)
        self.assertTrue(response["success"])
        # after creating contract - we can get contract details so as to get params
        # run calculation rules etc
        cd = ContractDetails.objects.filter(contract_id=response["data"]["id"]).first()
        # c = Contract.objects.filter(id=response["data"]["id"]).first()
        result_params = get_parameters("PolicyHolderInsuree", cd)

        # tear down the contract test data
        # cd.delete()
        # c.delete()

        # we want to assert name of param related to the contract details (should be 'income')
        # and also the value of contract (all contributions)
        # for that test should be income=500, 5 insurees, default rate=5 %
        # income*rate*number of contributions = according to Contribution Valuation Rule
        self.assertEqual(
            ("income", self.income * (float(self.rate / 100)) * self.number_of_insuree),
            (result_params[0]["name"], response["data"]["amount_notified"]),
        )

    def test_no_deatils(self):
        # create contract to test 1st calculation rule contribution valuation
        # test case - create contract and check if amount is calcutated properly
        # and test if on instance of contract details the proper params is showed
        # by getting param name
        contract = {
            "code": "CALTEST",
            "policy_holder_id": self.policy_holder.id,
            "date_valid_from": datetime.date(2017, 1, 1),
            "date_valid_to": datetime.date(2017, 1, 31),
        }

        response = self.contract_service.create(contract)
        self.assertTrue(response["success"])
        cd = ContractDetails.objects.filter(contract_id=response["data"]["id"]).first()
        self.assertIsNone(
            cd,
            "the contract should not have any detail as there is no insuree valid at this time",
        )
