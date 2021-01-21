import datetime
import numbers
import base64
from unittest import TestCase, mock
from uuid import UUID

import graphene
from contract.tests.helpers import *
from contract.models import Contract, ContractDetails
from policyholder.tests.helpers import *
from contribution_plan.tests.helpers import create_test_contribution_plan, \
    create_test_contribution_plan_bundle, create_test_contribution_plan_bundle_details
from contribution_plan.models import ContributionPlan, ContributionPlanBundle, ContributionPlanBundleDetails
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
        policy_holder = create_test_policy_holder()

        # create contribution plan etc
        contribution_plan_bundle = create_test_contribution_plan_bundle()
        contribution_plan = create_test_contribution_plan()
        contribution_plan_bundle_details = create_test_contribution_plan_bundle_details(
            contribution_plan=contribution_plan, contribution_plan_bundle=contribution_plan_bundle
        )

        # create policy holder insuree
        for i in range(0, 3):
            create_test_policy_holder_insuree(policy_holder=policy_holder,
                                              contribution_plan_bundle=contribution_plan_bundle)

        time_stamp = datetime.datetime.now()
        input_param = {
            "code": "XYZ:"+str(time_stamp),
            "policyHolderId": str(policy_holder.id)
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
        PolicyHolderInsuree.objects.filter(policy_holder_id=str(policy_holder.id)).delete()
        PolicyHolder.objects.filter(id=policy_holder.id).delete()
        ContributionPlanBundleDetails.objects.filter(id=contribution_plan_bundle_details.id).delete()
        ContributionPlanBundle.objects.filter(id=contribution_plan_bundle.id).delete()
        ContributionPlan.objects.filter(id=contribution_plan.id).delete()

        self.assertEqual(
            (
                "XYZ:"+str(time_stamp),
            )
            ,
            (
                result[0]['node']['code'],
            )
        )

    def test_mutation_contract_create_update_with_policy_holder(self):
        # create contract for contract with policy holder with two phinsuree
        policy_holder = create_test_policy_holder()

        # create contribution plan etc
        contribution_plan_bundle = create_test_contribution_plan_bundle()
        contribution_plan = create_test_contribution_plan()
        contribution_plan_bundle_details = create_test_contribution_plan_bundle_details(
            contribution_plan=contribution_plan, contribution_plan_bundle=contribution_plan_bundle
        )

        # create policy holder insuree
        for i in range(0, 3):
            create_test_policy_holder_insuree(policy_holder=policy_holder,
                                              contribution_plan_bundle=contribution_plan_bundle)

        time_stamp = datetime.datetime.now()
        input_param = {
            "code": "CT:"+str(time_stamp),
            "policyHolderId": str(policy_holder.id)
        }
        self.add_mutation("createContract", input_param)
        result = self.find_by_exact_attributes_query(
            "contract",
            params=input_param,
        )["edges"]
        converted_id = base64.b64decode(result[0]['node']['id']).decode('utf-8').split(':')[1]
        expected_amount_notified = result[0]["node"]["amountNotified"] + 400.50

        input_param = {
            "id": str(converted_id),
            "amountNotified": str(expected_amount_notified),
        }
        self.add_mutation("updateContract", input_param)
        result = self.find_by_exact_attributes_query(
            "contract",
            params={"id": str(converted_id)},
        )["edges"]

        # tear down the test data
        ContractDetails.objects.filter(contract_id=str(converted_id)).delete()
        Contract.objects.filter(id=str(converted_id)).delete()
        PolicyHolderInsuree.objects.filter(policy_holder_id=str(policy_holder.id)).delete()
        PolicyHolder.objects.filter(id=policy_holder.id).delete()
        ContributionPlanBundleDetails.objects.filter(id=contribution_plan_bundle_details.id).delete()
        ContributionPlanBundle.objects.filter(id=contribution_plan_bundle.id).delete()
        ContributionPlan.objects.filter(id=contribution_plan.id).delete()

        self.assertEqual(
            (
                expected_amount_notified,
            )
            ,
            (
                result[0]['node']['amountNotified'],
            )
        )

    def test_mutation_contract_create_details_and_update(self):
        # create contract for contract with policy holder with two phinsuree
        policy_holder = create_test_policy_holder()

        # create contribution plan etc
        contribution_plan_bundle = create_test_contribution_plan_bundle()
        contribution_plan = create_test_contribution_plan()
        contribution_plan_bundle_details = create_test_contribution_plan_bundle_details(
            contribution_plan=contribution_plan, contribution_plan_bundle=contribution_plan_bundle
        )

        # create policy holder insuree
        for i in range(0, 2):
            create_test_policy_holder_insuree(policy_holder=policy_holder,
                                              contribution_plan_bundle=contribution_plan_bundle)

        time_stamp = datetime.datetime.now()
        input_param = {
            "code": "CT:"+str(time_stamp),
            "policyHolderId": str(policy_holder.id)
        }
        self.add_mutation("createContract", input_param)
        result = self.find_by_exact_attributes_query(
            "contract",
            params=input_param,
        )["edges"]
        converted_id_contract = base64.b64decode(result[0]['node']['id']).decode('utf-8').split(':')[1]

        # scneario to create contract detail
        policy_holder_insuree = create_test_policy_holder_insuree(policy_holder=policy_holder,
                                                                   contribution_plan_bundle=contribution_plan_bundle)
        policy_holder_insuree2 = create_test_policy_holder_insuree(policy_holder=policy_holder,
                                                                   contribution_plan_bundle=contribution_plan_bundle)
        input_param = {
            "contractId": str(converted_id_contract),
            "insureeId": policy_holder_insuree.insuree.id,
            "contributionPlanBundleId": str(contribution_plan_bundle_details.id),
        }
        self.add_mutation("createContractDetails", input_param)
        result = self.find_by_exact_attributes_query(
            "contractDetails",
            params=input_param,
        )["edges"]
        converted_id = base64.b64decode(result[0]['node']['id']).decode('utf-8').split(':')[1]

        #in update contract detail test the scenario is to change insuree
        input_param = {
            "id": str(converted_id),
            "insureeId": policy_holder_insuree2.insuree.id,
        }
        self.add_mutation("updateContractDetails", input_param)
        result = self.find_by_exact_attributes_query(
            "contractDetails",
            params=input_param,
        )["edges"]
        converted_id = base64.b64decode(result[0]['node']['id']).decode('utf-8').split(':')[1]

        # tear down the test data
        ContractDetails.objects.filter(contract_id=str(converted_id_contract)).delete()
        Contract.objects.filter(id=str(converted_id_contract)).delete()
        PolicyHolderInsuree.objects.filter(policy_holder_id=str(policy_holder.id)).delete()
        PolicyHolder.objects.filter(id=policy_holder.id).delete()
        ContributionPlanBundleDetails.objects.filter(id=contribution_plan_bundle_details.id).delete()
        ContributionPlanBundle.objects.filter(id=contribution_plan_bundle.id).delete()
        ContributionPlan.objects.filter(id=contribution_plan.id).delete()

        self.assertEqual(2, result[0]['node']['version'])

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
        node_content_str = "\n".join(params.keys()) if query_type == "contract" else ''
        query = F'''
        {{
            {query_type}({ 'contract_Id: "'+str(params["contractId"])+'", orderBy: ["-dateCreated"]'  if "contractId" in params else self.build_params(params)}) {{
                totalCount
                edges {{
                  node {{
                    id
                    {node_content_str}
                    version
                    {'amountDue' if query_type =='contract' else '' }
                    {'amountNotified' if query_type =='contract' else '' }
                    {'amountRectified' if query_type =='contract' else '' }
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

