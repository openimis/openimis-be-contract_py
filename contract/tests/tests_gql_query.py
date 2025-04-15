import base64
import datetime
from unittest import mock
from uuid import UUID

import graphene
from django.test import TestCase
from graphene import Schema
from graphene.test import Client
from core.models import User
from core.test_helpers import create_test_interactive_user

from contract import schema as contract_schema
from contract.tests.helpers import (
    create_test_contract,
    create_test_contract_contribution_plan_details,
    create_test_contract_details,
)

from core.models.openimis_graphql_test_case import openIMISGraphQLTestCase, BaseTestContext

class ContractQueryTest(openIMISGraphQLTestCase):


    @classmethod
    def setUpClass(cls):
        super(ContractQueryTest, cls).setUpClass()
        cls.date_created = datetime.datetime.now()
        cls.test_contract = create_test_contract(
            custom_props={
                "code": "testContract-" + str(cls.date_created),
                "payment_reference": "payment reference" + str(cls.date_created),
                "amount_due": 450.99,
                "date_valid_from": datetime.date(2020, 1, 1),
                "amendment": 1,
            }
        )
        cls.test_contract_details = create_test_contract_details(
            contract=cls.test_contract
        )
        cls.test_contract_contribution_plan_details = (
            create_test_contract_contribution_plan_details(
                contract_details=cls.test_contract_details
            )
        )

        cls.schema = Schema(
            query=contract_schema.Query,
        )

        cls.graph_client = Client(cls.schema)
        cls.user = User.objects.filter(username="admin", i_user__isnull=False).first()
        if not cls.user:
            cls.user = create_test_interactive_user(username="admin")
        cls.user_context = BaseTestContext(cls.user)

    def test_find_contract_existing(self):
        id = self.test_contract.id
        result = self.find_by_id_query("contract", id)
        converted_id = (
            base64.b64decode(result[0]["node"]["id"]).decode("utf-8").split(":")[1]
        )
        self.assertEqual(UUID(converted_id), id)

    def test_find_contract_details_existing(self):
        id = self.test_contract_details.id
        result = self.find_by_id_query("contractDetails", id)
        converted_id = (
            base64.b64decode(result[0]["node"]["id"]).decode("utf-8").split(":")[1]
        )
        self.assertEqual(UUID(converted_id), id)

    def test_find_contract_contribution_plan_details_existing(self):
        id = self.test_contract_contribution_plan_details.id
        result = self.find_by_id_query("contractContributionPlanDetails", id)
        converted_id = (
            base64.b64decode(result[0]["node"]["id"]).decode("utf-8").split(":")[1]
        )
        self.assertEqual(UUID(converted_id), id)

    def test_find_contract_by_params(self):
        expected = self.test_contract
        params = {
            "version": expected.version,
            "isDeleted": True if expected.is_deleted else False,
            "code": expected.code,
        }
        result = self.find_by_exact_attributes_query("contract", params)
        self.assertDictEqual(result[0]["node"], params)

    def test_find_contract_details_by_contract(self):
        details_contract_id = self.test_contract_details.contract.id
        id = self.test_contract_details.id
        query = f"""
        {{
            contractDetails(
                contract_Id: "{details_contract_id}"){{
                totalCount
                edges {{
                  node {{
                    id
                  }}
                  cursor
                }}
          }}
        }}
        """
        query_result = self.execute_query(query)
        result = query_result["contractDetails"]["edges"][0]["node"]
        converted_id = base64.b64decode(result["id"]).decode("utf-8").split(":")[1]
        self.assertEqual(UUID(converted_id), id)

    def test_find_contract_details_by_id_and_insuree(self):
        details_insuree_uuid = self.test_contract_details.insuree.uuid
        id = self.test_contract_details.id
        query = f"""
        {{
            contractDetails(
                id: "{id}"
                insuree_Uuid: "{details_insuree_uuid}"){{
                totalCount
                edges {{
                  node {{
                    id
                  }}
                  cursor
                }}
          }}
        }}
        """
        query_result = self.execute_query(query)
        result = query_result["contractDetails"]["edges"][0]["node"]
        converted_id = base64.b64decode(result["id"]).decode("utf-8").split(":")[1]
        self.assertEqual(UUID(converted_id), id)

    def test_find_contract_by_contract_code(self):
        code = self.test_contract.code
        id = self.test_contract.id
        query = f"""
        {{
            contract(
                code: "{code}"){{
                totalCount
                edges {{
                  node {{
                    id
                  }}
                  cursor
                }}
          }}
        }}
        """
        query_result = self.execute_query(query)
        result = query_result["contract"]["edges"][0]["node"]
        converted_id = base64.b64decode(result["id"]).decode("utf-8").split(":")[1]
        self.assertEqual(UUID(converted_id), id)

    def test_find_contract_by_contract_payment_reference(self):
        payment_reference = self.test_contract.payment_reference
        id = self.test_contract.id
        query = f"""
        {{
            contract(
                paymentReference: "{payment_reference}"){{
                totalCount
                edges {{
                  node {{
                    id
                  }}
                  cursor
                }}
          }}
        }}
        """
        query_result = self.execute_query(query)
        result = query_result["contract"]["edges"][0]["node"]
        converted_id = base64.b64decode(result["id"]).decode("utf-8").split(":")[1]
        self.assertEqual(UUID(converted_id), id)

    def test_find_contract_by_contract_code_amount_due(self):
        code = self.test_contract.code
        amount_due = self.test_contract.amount_due
        id = self.test_contract.id
        query = f"""
        {{
            contract(
                code:" {code}", amountDue: {amount_due}){{
                totalCount
                edges {{
                  node {{
                    id
                  }}
                  cursor
                }}
          }}
        }}
        """
        query_result = self.execute_query(query)
        result = query_result["contract"]["edges"][0]["node"]
        converted_id = base64.b64decode(result["id"]).decode("utf-8").split(":")[1]
        self.assertEqual(UUID(converted_id), id)

    def test_find_contract_by_contract_code_amount_due_greater(self):
        code = self.test_contract.code
        amount_due = self.test_contract.amount_due - 100
        id = self.test_contract.id
        query = f"""
        {{
            contract(
                code:" {code}", amountDue_Gte: {amount_due}){{
                totalCount
                edges {{
                  node {{
                    id
                  }}
                  cursor
                }}
          }}
        }}
        """
        query_result = self.execute_query(query)
        result = query_result["contract"]["edges"][0]["node"]
        converted_id = base64.b64decode(result["id"]).decode("utf-8").split(":")[1]
        self.assertEqual(UUID(converted_id), id)

    def test_find_contract_by_contract_code_amount_due_greater_equal(self):
        code = self.test_contract.code
        amount_due = self.test_contract.amount_due
        id = self.test_contract.id
        query = f"""
        {{
            contract(
                code:" {code}", amountDue_Gte: {amount_due}){{
                totalCount
                edges {{
                  node {{
                    id
                  }}
                  cursor
                }}
          }}
        }}
        """
        query_result = self.execute_query(query)
        result = query_result["contract"]["edges"][0]["node"]
        converted_id = base64.b64decode(result["id"]).decode("utf-8").split(":")[1]
        self.assertEqual(UUID(converted_id), id)

    def test_find_contract_by_contract_code_amound_due_lt(self):
        code = self.test_contract.code
        amount_due = self.test_contract.amount_due
        # id = self.test_contract.id
        query = f"""
        {{
            contract(
                code:" {code}", amountDue_Lt: {amount_due}){{
                totalCount
                edges {{
                  node {{
                    id
                  }}
                  cursor
                }}
          }}
        }}
        """
        query_result = self.execute_query(query)
        result = query_result["contract"]["edges"]
        self.assertEqual(len(result), 0)

    def test_find_contract_by_insuree(self):
        details_insuree_uuid = self.test_contract_details.insuree.uuid
        id = self.test_contract.id
        query = f"""
        {{
            contract(
                insuree: "{details_insuree_uuid}") {{
                totalCount
                edges {{
                  node {{
                    id
                  }}
                  cursor
                }}
          }}
        }}
        """
        query_result = self.execute_query(query)
        result = query_result["contract"]["edges"][0]["node"]
        converted_id = base64.b64decode(result["id"]).decode("utf-8").split(":")[1]
        self.assertEqual(UUID(converted_id), id)

    def test_find_contract_by_id_and_state(self):
        details_contract_state = self.test_contract.state
        id = self.test_contract.id
        query = f"""
        {{
            contract(
                id: "{id}"
                state: {details_contract_state}) {{
                totalCount
                edges {{
                  node {{
                    id
                  }}
                  cursor
                }}
          }}
        }}
        """
        query_result = self.execute_query(query)
        result = query_result["contract"]["edges"][0]["node"]
        converted_id = base64.b64decode(result["id"]).decode("utf-8").split(":")[1]
        self.assertEqual(UUID(converted_id), id)

    def test_find_contract_contribution_plan_details_by_contract_details_and_contribution_plan(
        self,
    ):
        details_contract_details_id = (
            self.test_contract_contribution_plan_details.contract_details.id
        )
        details_contribution_plan_id = (
            self.test_contract_contribution_plan_details.contribution_plan.id
        )
        id = self.test_contract_contribution_plan_details.id
        query = f"""
        {{
            contractContributionPlanDetails(
                contractDetails_Id: "{details_contract_details_id}",
                contributionPlan_Id: "{details_contribution_plan_id}") {{
                totalCount
                edges {{
                  node {{
                    id
                  }}
                  cursor
                }}
          }}
        }}
        """
        query_result = self.execute_query(query)
        result = query_result["contractContributionPlanDetails"]["edges"][0]["node"]
        converted_id = base64.b64decode(result["id"]).decode("utf-8").split(":")[1]
        self.assertEqual(UUID(converted_id), id)

    def test_find_contract_by_contract_code_date_valid_from_gte(self):
        code = self.test_contract.code
        date_valid_from = str(self.test_contract.date_valid_from.date()) + "T00:00:00"
        id = self.test_contract.id
        query = f"""
        {{
            contract(
                code: "{code}", dateValidFrom_Gte: "{date_valid_from}"){{
                totalCount
                edges {{
                  node {{
                    id
                  }}
                  cursor
                }}
          }}
        }}
        """
        query_result = self.execute_query(query)
        result = query_result["contract"]["edges"][0]["node"]
        converted_id = base64.b64decode(result["id"]).decode("utf-8").split(":")[1]
        self.assertEqual(UUID(converted_id), id)

    def test_find_contract_by_contract_code_contains(self):
        date = self.date_created
        id = self.test_contract.id
        query = f"""
        {{
            contract(
                code_Icontains: "{date}"){{
                totalCount
                edges {{
                  node {{
                    id
                  }}
                  cursor
                }}
          }}
        }}
        """
        query_result = self.execute_query(query)
        result = query_result["contract"]["edges"][0]["node"]
        converted_id = base64.b64decode(result["id"]).decode("utf-8").split(":")[1]
        self.assertEqual(UUID(converted_id), id)

    def test_find_contract_by_code_amendment(self):
        code = self.test_contract.code
        amendment = self.test_contract.amendment
        id = self.test_contract.id
        query = f"""
        {{
            contract(
                code: "{code}", amendment: {amendment}){{
                totalCount
                edges {{
                  node {{
                    id
                  }}
                  cursor
                }}
          }}
        }}
        """
        query_result = self.execute_query(query)
        result = query_result["contract"]["edges"][0]["node"]
        converted_id = base64.b64decode(result["id"]).decode("utf-8").split(":")[1]
        self.assertEqual(UUID(converted_id), id)

    def test_find_contract_by_contract_code_start_with(self):
        query = f"""
        {{
            contract(
                code_Istartswith: "{'testContract-'}"){{
                totalCount
                edges {{
                  node {{
                    id
                  }}
                  cursor
                }}
          }}
        }}
        """
        query_result = self.execute_query(query)
        result = query_result["contract"]["edges"]
        self.assertGreater(len(result), 0)

    def test_find_contracts_details_by_date_created(self):
        date_created = str(self.test_contract_details.date_created).replace(" ", "T")
        id = self.test_contract_details.id
        query = f"""
        {{
            contractDetails(
                dateCreated: "{date_created}"){{
                totalCount
                edges {{
                  node {{
                    id
                  }}
                  cursor
                }}
          }}
        }}
        """
        query_result = self.execute_query(query)
        result = query_result["contractDetails"]["edges"][0]["node"]
        converted_id = base64.b64decode(result["id"]).decode("utf-8").split(":")[1]
        self.assertEqual(UUID(converted_id), id)

    def test_find_contracts_details_by_date_updated(self):
        date_updated = str(self.test_contract_details.date_updated).replace(" ", "T")
        id = self.test_contract_details.id
        query = f"""
        {{
            contractDetails(
                dateUpdated: "{date_updated}"){{
                totalCount
                edges {{
                  node {{
                    id
                  }}
                  cursor
                }}
          }}
        }}
        """
        query_result = self.execute_query(query)
        result = query_result["contractDetails"]["edges"][0]["node"]
        converted_id = base64.b64decode(result["id"]).decode("utf-8").split(":")[1]
        self.assertEqual(UUID(converted_id), id)

    def test_find_contract_contribution_plan_details_by_date_created(self):
        date_created = str(
            self.test_contract_contribution_plan_details.date_created
        ).replace(" ", "T")
        id = self.test_contract_contribution_plan_details.id
        query = f"""
        {{
            contractContributionPlanDetails(
                dateCreated: "{date_created}"){{
                totalCount
                edges {{
                  node {{
                    id
                  }}
                  cursor
                }}
          }}
        }}
        """
        query_result = self.execute_query(query)
        result = query_result["contractContributionPlanDetails"]["edges"][0]["node"]
        converted_id = base64.b64decode(result["id"]).decode("utf-8").split(":")[1]
        self.assertEqual(UUID(converted_id), id)

    def test_find_contract_contribution_plan_details_by_date_created_gte(self):
        date_created = str(
            self.test_contract_contribution_plan_details.date_created
        ).replace(" ", "T")
        id = self.test_contract_contribution_plan_details.id
        query = f"""
        {{
            contractContributionPlanDetails(
                dateCreated_Gte: "{date_created}"){{
                totalCount
                edges {{
                  node {{
                    id
                  }}
                  cursor
                }}
          }}
        }}
        """
        query_result = self.execute_query(query)
        result = query_result["contractContributionPlanDetails"]["edges"][0]["node"]
        converted_id = base64.b64decode(result["id"]).decode("utf-8").split(":")[1]
        self.assertEqual(UUID(converted_id), id)

    def test_find_contract_contribution_plan_details_by_date_created_gt(self):
        date_created = str(
            self.test_contract_contribution_plan_details.date_created
        ).replace(" ", "T")
        # id = self.test_contract_contribution_plan_details.id
        query = f"""
        {{
            contractContributionPlanDetails(
                dateCreated_Gt: "{date_created}"){{
                totalCount
                edges {{
                  node {{
                    id
                  }}
                  cursor
                }}
          }}
        }}
        """
        query_result = self.execute_query(query)
        result = query_result["contractContributionPlanDetails"]["edges"]
        self.assertEqual(len(result), 0)

    def test_find_contract_contribution_plan_details_by_date_updated(self):
        date_updated = str(
            self.test_contract_contribution_plan_details.date_updated
        ).replace(" ", "T")
        id = self.test_contract_contribution_plan_details.id
        query = f"""
        {{
            contractContributionPlanDetails(
                dateUpdated: "{date_updated}"){{
                totalCount
                edges {{
                  node {{
                    id
                  }}
                  cursor
                }}
          }}
        }}
        """
        query_result = self.execute_query(query)
        result = query_result["contractContributionPlanDetails"]["edges"][0]["node"]
        converted_id = base64.b64decode(result["id"]).decode("utf-8").split(":")[1]
        self.assertEqual(UUID(converted_id), id)

    def test_find_contract_contribution_plan_details_by_id_and_contribution(self):
        details_contribution_uuid = (
            self.test_contract_contribution_plan_details.contribution.uuid
        )
        id = self.test_contract_contribution_plan_details.id
        query = f"""
        {{
            contractContributionPlanDetails(
                id: "{id}"
                contribution_Uuid: "{details_contribution_uuid}"){{
                totalCount
                edges {{
                  node {{
                    id
                  }}
                  cursor
                }}
          }}
        }}
        """
        query_result = self.execute_query(query)
        result = query_result["contractContributionPlanDetails"]["edges"][0]["node"]
        converted_id = base64.b64decode(result["id"]).decode("utf-8").split(":")[1]
        self.assertEqual(UUID(converted_id), id)

    def test_find_contract_contribution_plan_details_by_id_and_amount_in_contribution_gte(
        self,
    ):
        details_contribution_amount = (
            self.test_contract_contribution_plan_details.contribution.amount
        )
        id = self.test_contract_contribution_plan_details.id
        query = f"""
        {{
            contractContributionPlanDetails(
                id: "{id}"
                contribution_Amount_Gte: "{details_contribution_amount}"){{
                totalCount
                edges {{
                  node {{
                    id
                  }}
                  cursor
                }}
          }}
        }}
        """
        query_result = self.execute_query(query)
        result = query_result["contractContributionPlanDetails"]["edges"][0]["node"]
        converted_id = base64.b64decode(result["id"]).decode("utf-8").split(":")[1]
        self.assertEqual(UUID(converted_id), id)

    def test_find_contract_contribution_plan_details_by_id_and_amount_in_contribution_gt(
        self,
    ):
        details_contribution_amount = (
            self.test_contract_contribution_plan_details.contribution.amount
        )
        id = self.test_contract_contribution_plan_details.id
        query = f"""
        {{
            contractContributionPlanDetails(
                id: "{id}"
                contribution_Amount_Gt: "{details_contribution_amount}"){{
                totalCount
                edges {{
                  node {{
                    id
                  }}
                  cursor
                }}
          }}
        }}
        """
        query_result = self.execute_query(query)
        result = query_result["contractContributionPlanDetails"]["edges"]
        self.assertEqual(len(result), 0)

    def test_find_contract_contribution_plan_details_by_insuree(self):
        details_insuree_uuid = self.test_contract_details.insuree.uuid
        id = self.test_contract_contribution_plan_details.id
        query = f"""
        {{
            contractContributionPlanDetails(
                insuree: "{details_insuree_uuid}") {{
                totalCount
                edges {{
                  node {{
                    id
                  }}
                  cursor
                }}
          }}
        }}
        """
        query_result = self.execute_query(query)
        result = query_result["contractContributionPlanDetails"]["edges"][0]["node"]
        converted_id = base64.b64decode(result["id"]).decode("utf-8").split(":")[1]
        self.assertEqual(UUID(converted_id), id)

    def find_by_id_query(self, query_type, id, context=None):
        query = f"""
        {{
            {query_type}(id:"{id}") {{
                totalCount
                edges {{
                  node {{
                    id
                  }}
                  cursor
                }}
          }}
        }}
        """

        query_result = self.execute_query(query, context=context)
        records = query_result[query_type]["edges"]

        if len(records) > 1:
            raise ValueError(f"Ambiguous id {id} for query {query_type}")

        return records

    def find_by_exact_attributes_query(self, query_type, params, context=None):
        node_content_str = "\n".join(params.keys())
        query = f"""
        {{
            {query_type}({self.build_params(params)}) {{
                totalCount
                edges {{
                  node {{
                    {node_content_str}
                  }}
                  cursor
                }}
          }}
        }}
        """
        query_result = self.execute_query(query, context=context)
        records = query_result[query_type]["edges"]
        return records

    def execute_query(self, query, context=None):
        if context is None:
            self.user_context.data = query
            context = self.user_context.get_request()

        query_result = self.graph_client.execute(query, context=context)
        query_data = query_result["data"]
        return query_data

    def build_params(self, params):
        def wrap_arg(v):
            if isinstance(v, str):
                return f'"{v}"'
            if isinstance(v, bool):
                return str(v).lower()
            if isinstance(v, datetime.date):
                return graphene.DateTime.serialize(
                    datetime.datetime.fromordinal(v.toordinal())
                )
            return v

        params_as_args = [f"{k}:{wrap_arg(v)}" for k, v in params.items()]
        return ", ".join(params_as_args)
