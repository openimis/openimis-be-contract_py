import datetime
import numbers
import base64
from unittest import TestCase, mock
from uuid import UUID

import graphene
from contract.tests.helpers import *
from contract import schema as contract_schema
from graphene import Schema
from graphene.test import Client


class ContractQueryTest(TestCase):

    class BaseTestContext:
        user = mock.Mock(is_anonymous=False)
        user.has_perm = mock.MagicMock(return_value=False)

    class AnonymousUserContext:
        user = mock.Mock(is_anonymous=True)

    @classmethod
    def setUpClass(cls):
        cls.test_contract = create_test_contract(
            custom_props={'code': 'testContract'})
        cls.test_contract_details = create_test_contract_details()
        cls.test_contract_contribution_plan_details = create_test_contract_contribution_plan_details()

        cls.schema = Schema(
            query=contract_schema.Query,
        )

        cls.graph_client = Client(cls.schema)

    def test_find_contract_existing(self):
        id = self.test_contract.id
        result = self.find_by_id_query("contract", id)
        converted_id = base64.b64decode(result[0]['node']['id']).decode('utf-8').split(':')[1]
        self.assertEqual(UUID(converted_id), id)

    def test_find_contract_details_existing(self):
        id = self.test_contract_details.id
        result = self.find_by_id_query("contractDetails", id)
        converted_id = base64.b64decode(result[0]['node']['id']).decode('utf-8').split(':')[1]
        self.assertEqual(UUID(converted_id), id)

    def test_find_contract_contribution_plan_details_existing(self):
        id = self.test_contract_contribution_plan_details.id
        result = self.find_by_id_query("contractContributionPlanDetails", id)
        converted_id = base64.b64decode(result[0]['node']['id']).decode('utf-8').split(':')[1]
        self.assertEqual(UUID(converted_id), id)

    def test_find_contract_by_params(self):
        expected = self.test_contract
        params = {
            'version': expected.version,
            'isDeleted': True if expected.is_deleted else False,
            'code': expected.code,
        }
        result = self.find_by_exact_attributes_query("contract", params)
        self.assertDictEqual(result[0]['node'], params)

    def test_find_contract_details_by_contract(self):
        details_insuree_chf_id = self.test_contract_details.insuree.chf_id
        details_contract_id = self.test_contract_details.contract.id
        id = self.test_contract_details.id
        query = F'''
        {{
            contractDetails(
                contract_Id:"{details_contract_id}"){{
                totalCount
                edges {{
                  node {{
                    id
                  }}
                  cursor
                }}
          }}
        }}
        '''
        query_result = self.execute_query(query)
        result = query_result['contractDetails']['edges'][0]['node']
        converted_id = base64.b64decode(result['id']).decode('utf-8').split(':')[1]
        self.assertEqual(UUID(converted_id), id)

    def test_find_contract_contribution_plan_details_by_contract_details_and_contribution_plan(self):
        details_contract_details_id = self.test_contract_contribution_plan_details.contract_details.id
        details_contribution_plan_id = self.test_contract_contribution_plan_details.contribution_plan.id
        id = self.test_contract_contribution_plan_details.id
        query = F'''
        {{
            contractContributionPlanDetails(
                contractDetails_Id:"{details_contract_details_id}",
                contributionPlan_Id:"{details_contribution_plan_id}") {{
                totalCount
                edges {{
                  node {{
                    id
                  }}
                  cursor
                }}
          }}
        }}
        '''
        query_result = self.execute_query(query)
        result = query_result['contractContributionPlanDetails']['edges'][0]['node']
        converted_id = base64.b64decode(result['id']).decode('utf-8').split(':')[1]
        self.assertEqual(UUID(converted_id), id)

    def find_by_id_query(self, query_type, id, context=None):
        query = F'''
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
        '''

        query_result = self.execute_query(query, context=context)
        records = query_result[query_type]['edges']

        if len(records) > 1:
            raise ValueError(F"Ambiguous id {id} for query {query_type}")

        return records

    def find_by_exact_attributes_query(self, query_type, params, context=None):
        node_content_str = "\n".join(params.keys())
        query = F'''
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
        '''
        query_result = self.execute_query(query, context=context)
        records = query_result[query_type]['edges']
        return records

    def execute_query(self, query, context=None):
        if context is None:
            context = self.BaseTestContext()

        query_result = self.graph_client.execute(query, context=context)
        query_data = query_result['data']
        return query_data

    def build_params(self, params):
        def wrap_arg(v):
            if isinstance(v, str):
                return F'"{v}"'
            if isinstance(v, bool):
                return str(v).lower()
            if isinstance(v, datetime.date):
                return graphene.DateTime.serialize(
                    datetime.datetime.fromordinal(v.toordinal()))
            return v

        params_as_args = [f'{k}:{wrap_arg(v)}' for k, v in params.items()]
        return ", ".join(params_as_args)