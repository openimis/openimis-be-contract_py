import datetime
import numbers
import base64
from unittest import TestCase, mock
from uuid import UUID

import graphene
from contract.tests.helpers import *
from contract.models import Contract, ContractDetails
from policyholder.tests.helpers import *
from policyholder.models import PolicyHolder, PolicyHolderInsuree
from contract import schema as contract_schema
from graphene import Schema
from graphene.test import Client


class MutationTestCreate(TestCase):

    class BaseTestContext:
        user = User.objects.get(username="admin")

    class AnonymousUserContext:
        user = mock.Mock(is_anonymous=True)

    @classmethod
    def setUpClass(cls):

        cls.schema = Schema(
            query=contract_schema.Query,
            mutation=contract_schema.Mutation
        )

        cls.graph_client = Client(cls.schema)

    def test_mutation_contract_create_without_policy_holder(self):
        time_stamp = datetime.datetime.now()
        input_param = {
            "code": "XYZ:"+str(time_stamp),
        }
        self.add_mutation("createContract", input_param)
        result = self.find_by_exact_attributes_query(
            "contract",
            params=input_param,
        )["edges"]
        converted_id = base64.b64decode(result[0]['node']['id']).decode('utf-8').split(':')[1]
        # tear down the test data
        Contract.objects.filter(id=str(converted_id)).delete()
        self.assertEqual(
            (
                "XYZ:"+str(time_stamp),
            )
            ,
            (
                result[0]['node']['code'],
            )
        )

    def test_mutation_contract_create_with_policy_holder(self):
        # create contract for contract with policy holder with two phinsuree
        test_policy_holder = create_test_policy_holder()
        test_policy_holder_insuree = create_test_policy_holder_insuree(policy_holder=test_policy_holder)
        test_policy_holder_insuree2 = create_test_policy_holder_insuree(policy_holder=test_policy_holder)

        time_stamp = datetime.datetime.now()
        input_param = {
            "code": "XYZ:"+str(time_stamp),
            "policyHolderId": str(test_policy_holder.id)
        }
        self.add_mutation("createContract", input_param)
        result = self.find_by_exact_attributes_query(
            "contract",
            params=input_param,
        )["edges"]
        converted_id = base64.b64decode(result[0]['node']['id']).decode('utf-8').split(':')[1]
        # tear down the test data
        ContractDetails.objects.filter(contract_id=str(converted_id)).delete()
        Contract.objects.filter(id=str(converted_id)).delete()
        PolicyHolderInsuree.objects.filter(policy_holder_id=str(test_policy_holder.id)).delete()
        PolicyHolder.objects.filter(id=test_policy_holder.id).delete()

        self.assertEqual(
            (
                "XYZ:"+str(time_stamp),
            )
            ,
            (
                result[0]['node']['code'],
            )
        )

    def find_by_id_query(self, query_type, id, context=None):
        query = F'''
        {{
            {query_type}(id:"{id}") {{
                totalCount
                edges {{
                  node {{
                    id
                    version
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
        if "dateValidFrom" in params:
            params.pop('dateValidFrom')
        if "dateValidTo" in params:
            params.pop('dateValidTo')
        if "policyHolderId" in params:
            params.pop('policyHolderId')
        node_content_str = "\n".join(params.keys())
        query = F'''
        {{
            {query_type}({self.build_params(params)}) {{
                totalCount
                edges {{
                  node {{
                    {'id' if 'id' not in params else '' }
                    {node_content_str}
                    version
                    dateValidFrom
                    dateValidTo
                    replacementUuid
                  }}
                  cursor
                }}
          }}
        }}
        '''
        query_result = self.execute_query(query, context=context)
        records = query_result[query_type]
        return records

    def execute_query(self, query, context=None):
        if context is None:
            context = self.BaseTestContext()

        query_result = self.graph_client.execute(query, context=context)
        query_data = query_result['data']
        return query_data

    def add_mutation(self, mutation_type, input_params, context=None):
        mutation = f'''
        mutation 
        {{
            {mutation_type}(input: {{
               {self.build_params(input_params)}
            }})  

          {{
            internalId
            clientMutationId
          }}
        }}
        '''
        mutation_result = self.execute_mutation(mutation, context=context)
        return mutation_result

    def execute_mutation(self, mutation, context=None):
        if context is None:
            context = self.BaseTestContext()

        mutation_result = self.graph_client.execute(mutation, context=context)
        return mutation_result

    def build_params(self, params):
        def wrap_arg(v):
            if isinstance(v, str):
                return F'"{v}"'
            if isinstance(v, list):
                return json.dumps(v)
            if isinstance(v, bool):
                return str(v).lower()
            if isinstance(v, datetime.date):
                return graphene.DateTime.serialize(
                    datetime.datetime.fromordinal(v.toordinal()))
            return v

        params_as_args = [f'{k}:{wrap_arg(v)}' for k, v in params.items()]
        return ", ".join(params_as_args)

