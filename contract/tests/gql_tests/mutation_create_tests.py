import base64
from unittest import mock
from django.test import TestCase

import graphene
from contract.tests.helpers import *
from contract.models import Contract, ContractDetails
from core.models import TechnicalUser
from core.test_helpers import create_test_technical_user
from policyholder.tests.helpers import *
from contribution_plan.tests.helpers import create_test_contribution_plan, \
    create_test_contribution_plan_bundle, create_test_contribution_plan_bundle_details
from contract import schema as contract_schema
from graphene import Schema
from graphene.test import Client


class MutationTestContract(TestCase):
    class BaseTestContext:
        def __init__(self, user):
            self.user = user

    class AnonymousUserContext:
        user = mock.Mock(is_anonymous=True)

    @classmethod
    def setUpClass(cls):
        super(MutationTestContract, cls).setUpClass()
        if not TechnicalUser.objects.filter(username='admin').exists():
            create_test_technical_user(username='admin', password='S\/pe®Pąßw0rd™', super_user=True)
        cls.user = User.objects.filter(username='admin').first()
        # some test data so as to created contract properly
        cls.income = 500
        cls.rate = 5
        cls.number_of_insuree = 2
        cls.policy_holder = create_test_policy_holder()
        cls.policy_holder2 = create_test_policy_holder()
        # create contribution plans etc
        cls.contribution_plan_bundle = create_test_contribution_plan_bundle()
        cls.contribution_plan = create_test_contribution_plan(
            custom_props={"json_ext": {"calculation_rule": {"rate": cls.rate}}}
        )
        cls.contribution_plan_bundle_details = create_test_contribution_plan_bundle_details(
            contribution_plan=cls.contribution_plan,
            contribution_plan_bundle=cls.contribution_plan_bundle
        )
        from core import datetime
        # create policy holder insuree for that test policy holder
        for i in range(0, cls.number_of_insuree):
            ph_insuree = create_test_policy_holder_insuree(
                policy_holder=cls.policy_holder,
                contribution_plan_bundle=cls.contribution_plan_bundle,
                custom_props={
                    "last_policy": None,
                    "json_ext": {"calculation_rule": {"income": cls.income}}
                }
            )
            create_test_policy(
                cls.contribution_plan.benefit_plan,
                ph_insuree.insuree,
                custom_props={
                    "start_date": datetime.datetime(2016, 3, 1),
                    "expiry_date": datetime.datetime(2021, 7, 1)
                }
            )

        cls.policy_holder_insuree = create_test_policy_holder_insuree(
            policy_holder=cls.policy_holder,
            contribution_plan_bundle=cls.contribution_plan_bundle
        )
        cls.policy_holder_insuree2 = create_test_policy_holder_insuree(
            policy_holder=cls.policy_holder,
            contribution_plan_bundle=cls.contribution_plan_bundle
        )

        cls.schema = Schema(
            query=contract_schema.Query,
            mutation=contract_schema.Mutation
        )
        cls.graph_client = Client(cls.schema)

    def test_mutation_contract_create_without_policy_holder(self):
        time_stamp = datetime.datetime.now()
        input_param = {
            "code": "XYZ:" + str(time_stamp),
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
                "XYZ:" + str(time_stamp),
            )
            ,
            (
                result[0]['node']['code'],
            )
        )

    def test_mutation_contract_create_with_policy_holder(self):
        time_stamp = datetime.datetime.now()
        input_param = {
            "code": "XYZ:" + str(time_stamp),
            "policyHolderId": str(self.policy_holder.id)
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

        self.assertEqual(
            (
                "XYZ:" + str(time_stamp),
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
        if "contributionPlanBundleId" in params:
            params.pop('contributionPlanBundleId')
        if "insureeId" in params:
            params.pop('insureeId')
        if "uuids" in params:
            params["id"] = params["uuids"][0]
            params.pop("uuids")
        node_content_str = "\n".join(params.keys()) if query_type == "contract" else ''
        query = F'''
        {{
            {query_type}({'contract_Id: "' + str(params["contractId"]) + '", orderBy: ["-dateCreated"]' if "contractId" in params else self.build_params(params)}) {{
                totalCount
                edges {{
                  node {{
                    id
                    {node_content_str}
                    version
                    {'amountDue' if query_type == 'contract' else ''}
                    {'amountNotified' if query_type == 'contract' else ''}
                    {'amountRectified' if query_type == 'contract' else ''}
                    {'state' if query_type == 'contract' else ''}
                    {'paymentReference' if query_type == 'contract' else ''}
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
            context = self.BaseTestContext(self.user)

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
            context = self.BaseTestContext(self.user)

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
