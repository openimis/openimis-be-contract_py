import base64
import datetime
import json
import uuid
from unittest import mock

import graphene
from contribution_plan.tests.helpers import (
    create_test_contribution_plan,
    create_test_contribution_plan_bundle,
    create_test_contribution_plan_bundle_details,
)
from core.models import User, Role, RoleRight
from core.models.openimis_graphql_test_case import openIMISGraphQLTestCase, BaseTestContext
from core.test_helpers import create_test_interactive_user
from django.conf import settings
from graphene import Schema
from graphene.test import Client
from graphql_jwt.shortcuts import get_token
from policy.test_helpers import create_test_policy
from policyholder.tests.helpers import (
    create_test_policy_holder,
    create_test_policy_holder_insuree,
)
from policyholder.models import PolicyHolderUser
from contract import schema as contract_schema
from contract.models import Contract, ContractContributionPlanDetails
from contract.services import subtract_date_ranges
from contract.signals import append_contract_filter
from payment.models import Payment
from insuree.models import InsureePolicy
from core.utils import filter_validity

class MutationTestContract(openIMISGraphQLTestCase):
    GRAPHQL_URL = f"/{settings.SITE_ROOT()}graphql"
    # This is required by some version of graphene but is never used. It should be set to the schema but the import
    # is shown as an error in the IDE, so leaving it as True.
    GRAPHQL_SCHEMA = True
    user = None
    portal_user = None
    schema = Schema(query=contract_schema.Query)


    @classmethod
    def setUpClass(cls):
        super(MutationTestContract, cls).setUpClass()
        cls.user = User.objects.filter(username="admin", i_user__isnull=False).first()
        cls.policy_holder = create_test_policy_holder()
        if not cls.user:
            cls.user = create_test_interactive_user(username="admin")
        if not cls.portal_user:
            portal_role = Role.objects.create(
                name="portal",
                is_system=False,
                is_blocked=False
            )
            rights_id = [
                154402,
                154406,
                154404,
                153001,
                154403,
                154106,
                154203,
                154209,
                154207,
                154601,
                154101,
                154001,
                154401,
                154901,
                154202,
                154201,
                154104,
                154102,
                154501,
                154103
            ]
        
            for right_id in rights_id:
                RoleRight(
                    role_id=portal_role.id,
                    right_id=right_id,
                    audit_user_id=None,
                ).save()
            cls.portal_user = create_test_interactive_user(username="portal", roles = [portal_role.id])
            phu = PolicyHolderUser(
                user=cls.portal_user,
                date_valid_from=datetime.datetime.now(),
                policy_holder=cls.policy_holder
            )
            phu.save(user=cls.user)
        # some test data so as to created contract properly
        cls.user_context = BaseTestContext(user=cls.user)
        cls.user_token = cls.user_context.get_jwt()
        cls.user_portal_context = BaseTestContext(user=cls.portal_user)
        cls.user_portal_token =  cls.user_portal_context.get_jwt()
        
        cls.income = 500
        cls.rate = 5
        cls.number_of_insuree = 2
        cls.policy_holder2 = create_test_policy_holder()
        cls.time_stamp = datetime.datetime.now()
        cls.date_from = str((cls.time_stamp + datetime.timedelta(days=30)).date())
        cls.date_to = str((cls.time_stamp + datetime.timedelta(days=60)).date())
        # create contribution plans etc
        cls.contribution_plan_bundle = create_test_contribution_plan_bundle()

        cls.contribution_plan = create_test_contribution_plan(
            custom_props={
                "json_ext": {"calculation_rule": {"rate": cls.rate, "includeFamily": True} },
                "date_valid_from": "2010-01-01",
                "date_valid_to": "2020-01-01",
            }
        )
        cls.contribution_plan_old = create_test_contribution_plan(
            custom_props={
                "json_ext": {"calculation_rule": {"rate": cls.rate, "includeFamily": True}},
                "date_valid_from": "2020-01-01",
                "replacement_uuid": cls.contribution_plan.id
            }
        )

        cls.contribution_plan_bundle_details = create_test_contribution_plan_bundle_details(
            contribution_plan=cls.contribution_plan,
            contribution_plan_bundle=cls.contribution_plan_bundle
        )
        cls.contribution_plan_bundle_details = create_test_contribution_plan_bundle_details(
            contribution_plan=cls.contribution_plan_old,
            contribution_plan_bundle=cls.contribution_plan_bundle
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

        cls.policy_holder_insuree_old = create_test_policy_holder_insuree(
            policy_holder=cls.policy_holder,
            contribution_plan_bundle=cls.contribution_plan_bundle,
            custom_props={
                "json_ext": {"calculation_rule": {"income": cls.income}},
                "date_valid_from": "2010-01-01",
                "date_valid_to": "2020-01-01",
            }
        )

        cls.policy_holder_insuree = create_test_policy_holder_insuree(
            policy_holder=cls.policy_holder,
            contribution_plan_bundle=cls.contribution_plan_bundle,
            custom_props={
                "json_ext": {"calculation_rule": {"income": cls.income}},
                "date_valid_from": "2020-01-01",
                "replacement_uuid": cls.contribution_plan.id
            }
        )

        cls.policy_holder_insuree2 = create_test_policy_holder_insuree(
            policy_holder=cls.policy_holder,
            contribution_plan_bundle=cls.contribution_plan_bundle,
            custom_props={
                "json_ext": {"calculation_rule": {"income": cls.income}},
            }
        )

        cls.schema = Schema(
            query=contract_schema.Query, mutation=contract_schema.Mutation
        )
        cls.graph_client = Client(cls.schema)

    def test_mutation_contract_create_without_policy_holder(self):
        
        input_param = {
            "code": "XYZ:" + str(self.time_stamp),
            "dateValidFrom": self.date_from,
            "dateValidTo": self.date_to,
        }
        self.add_mutation("createContract", input_param, self.user_token)
        result = self.find_by_exact_attributes_query(
            "contract",
            params=input_param,
        )["edges"]
        # converted_id = base64.b64decode(result[0]['node']['id']).decode('utf-8').split(':')[1]
        # tear down the test data
        # Contract.objects.filter(id=str(converted_id)).delete()
        self.assertEqual(("XYZ:" + str(self.time_stamp),), (result[0]["node"]["code"],))

    def test_mutation_contract_create_with_policy_holder(self):
        #with mock.patch('django.db.transaction.on_commit', lambda func: func()):
            input_param = {
                "code": "XYZ:" + str(self.time_stamp),
                "policyHolderId": str(self.policy_holder.id),
                "clientMutationId": str(uuid.uuid4()),
                "dateValidFrom": self.date_from,
                "dateValidTo": self.date_to,
            }
            content = self.send_mutation("createContract", input_param, self.user_token)
            self.assertEqual(
                content["data"]["mutationLogs"]["edges"][0]["node"]["status"], 2
            )
            del input_param["clientMutationId"]
            result = self.find_by_exact_attributes_query(
                "contract",
                params=input_param,
            )["edges"]
            converted_id = (
                base64.b64decode(result[0]["node"]["id"]).decode("utf-8").split(":")[1]
            )
            # SUBMIT
            input_param = {"id": converted_id, "clientMutationId": str(uuid.uuid4())}
            content = self.send_mutation("submitContract", input_param, self.user_portal_token)
            content = self.assertEqual(
                content["data"]["mutationLogs"]["edges"][0]["node"]["status"], 2
            )

            # COUNTER
            input_param = {"id": converted_id, "clientMutationId": str(uuid.uuid4())}
            content = self.send_mutation("counterContract", input_param, self.user_token)

            content = self.assertEqual(
                content["data"]["mutationLogs"]["edges"][0]["node"]["status"], 2
            )

            # reSUBMIT
            input_param = {"id": converted_id, "clientMutationId": str(uuid.uuid4())}
            content = self.send_mutation("submitContract", input_param, self.user_token)
            self.assertEqual(
                content["data"]["mutationLogs"]["edges"][0]["node"]["status"], 2
            )
            # Approve
            input_param = {"id": converted_id, "clientMutationId": str(uuid.uuid4())}
            content = self.send_mutation("approveContract", input_param, self.user_token)

            self.assertEqual(
                content["data"]["mutationLogs"]["edges"][0]["node"]["status"], 2
            )
            # Pay
            contract = Contract.objects.get(id=converted_id)
            payment = Payment.objects.filter(
                append_contract_filter(
                    None,
                    user=self.user,
                    additional_filter={
                        'contract': contract.id
                    }
                ),
                *filter_validity()
            ).first()
            input_param = {
                "uuid": str(payment.uuid),
                "clientMutationId": str(uuid.uuid4()),
                "receivedAmount": str(payment.expected_amount),
                "expectedAmount": str(payment.expected_amount),
                "receiptNo": "tests",
                "typeOfPayment": "C",
            }
            content = self.send_mutation("updatePayment", input_param, self.user_token)
            self.assertEqual(
                content["data"]["mutationLogs"]["edges"][0]["node"]["status"], 2
            )
            contract.refresh_from_db()
            self.assertEqual(contract.state, Contract.STATE_EFFECTIVE, 'contract not effective')
            insuree_policies = list(InsureePolicy.objects.filter(policy__in=ContractContributionPlanDetails.objects.filter(
                contract_details__contract=contract
            ).values_list('policy_id', flat=True)))

            for d in list(contract.contractdetails_set.all()):
                ips = [ip for ip in insuree_policies if ip.insuree_id == d.insuree_id]
                self.assertTrue(len(ips) > 0)
                not_covered = subtract_date_ranges(
                    (contract.date_valid_from, contract.date_valid_to,),
                    [(ip.effective_date, ip.expiry_date,) for ip in ips]
                )
                self.assertTrue(not_covered == [])

            # check the contract details

            query = f"""
        {{
        contractContributionPlanDetails(contractDetails_Contract_Id: "{
            str(contract.id)}",isDeleted: false,first: 10,orderBy: ["contractDetails_Insuree_Uuid"])
        {{
            totalCount

        pageInfo {{ hasNextPage, hasPreviousPage, startCursor, endCursor}}
        edges
        {{
        node
        {{
            jsonExt,contractDetails{{
                id,
                jsonExt,
                contract{{id}},
                insuree{{id, uuid, chfId, lastName, otherNames, dob}},
                contributionPlanBundle{{
                    id, code, name, periodicity,
                    dateValidFrom, dateValidTo,
                    isDeleted, replacementUuid
                }}
            }},
            contributionPlan{{id, code, name}}
        }}
        }}
        }}
        }}
            """

            response = self.query(
                query,
                headers={"HTTP_AUTHORIZATION": f"Bearer {self.user_token}"},
            )
            content = json.loads(response.content)['data']
            self.assertEqual(len(content["contractContributionPlanDetails"]["edges"]),
                            4, "number of detail is not as expected")

            # check covered persons query

            query = f"""
        {{
        insureePolicy(additionalFilter: "{{\\"contract\\":\\"{str(contract.id)}\\"}}",first: 10,orderBy: ["insuree"])
        {{
            totalCount
            pageInfo {{ hasNextPage, hasPreviousPage, startCursor, endCursor}}
            edges
            {{
            node
            {{
                insuree{{id, uuid, chfId, lastName, otherNames, dob}}
            }}
            }}
        }}
        }}
            """
            response = self.query(
                query,
                headers={"HTTP_AUTHORIZATION": f"Bearer {self.user_token}"},
            )
            content = json.loads(response.content)['data']
            self.assertEqual(len(content["insureePolicy"]["edges"]), 4, "number of insuree Policy is not as expected")

    def find_by_id_query(self, query_type, id, context=None):
            query = f"""
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
            """

            query_result = self.execute_query(query, context=context)
            records = query_result[query_type]["edges"]

            if len(records) > 1:
                raise ValueError(f"Ambiguous id {id} for query {query_type}")

            return records

    def find_by_exact_attributes_query(self, query_type, params, context=None):
        if "dateValidFrom" in params:
            params.pop("dateValidFrom")
        if "clientMutationId" in params:
            params.pop("clientMutationId")
        if "dateValidTo" in params:
            params.pop("dateValidTo")
        if "policyHolderId" in params:
            params.pop("policyHolderId")
        if "contributionPlanBundleId" in params:
            params.pop("contributionPlanBundleId")
        if "insureeId" in params:
            params.pop("insureeId")
        if "uuids" in params:
            params["id"] = params["uuids"][0]
            params.pop("uuids")
        node_content_str = "\n".join(params.keys()) if query_type == "contract" else ""
        query = f"""
        {{
            {query_type}({'contract_Id: "' + str(params["contractId"])
                + '", orderBy: ["-dateCreated"]' if "contractId" in params else self.build_params(params)}) {{
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
        """
        query_result = self.execute_query(query, context=context)
        records = query_result[query_type]
        return records

    def execute_query(self, query, context=None):
        if context is None:
            context = BaseTestContext(self.user).get_request()

        query_result = self.graph_client.execute(query, context=context)
        query_data = query_result["data"]
        return query_data

    def add_mutation(self, mutation_type, input_params, context=None):

        if "clientMutationId" not in input_params:
            input_params["clientMutationId"] = str(uuid.uuid4())
        mutation = f"""
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
        """
        mutation_result = self.query(
            mutation,
            headers={"HTTP_AUTHORIZATION": f"Bearer {self.user_token}"},
        )
        self.assertResponseNoErrors(mutation_result)
        content = json.loads(mutation_result.content)
        return content

    def execute_mutation(self, mutation, context=None):
        if context is None:
            context = BaseTestContext(self.user)

        mutation_result = self.graph_client.execute(mutation, context=context)
        return mutation_result

    def build_params(self, params):
        def wrap_arg(v):
            if isinstance(v, str):
                return f'"{v}"'
            if isinstance(v, list):
                return json.dumps(v)
            if isinstance(v, bool):
                return str(v).lower()
            if isinstance(v, datetime.date):
                return graphene.DateTime.serialize(
                    datetime.datetime.fromordinal(v.toordinal())
                )
            return v

        params_as_args = [f"{k}:{wrap_arg(v)}" for k, v in params.items()]
        return ", ".join(params_as_args)
