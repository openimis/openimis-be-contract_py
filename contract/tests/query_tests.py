# import datetime
# import json
#
# import contract.schema as contract_schema
# from contract.models import Contract
# from contract.tests.helpers import create_test_contract
# from core.models import InteractiveUser
# from django.test import TestCase
# from unittest.mock import Mock, patch
# from graphene.test import Client
# from policyholder import PolicyHolder
#
#
# class ContractTest(TestCase):
#
#     def setUp(self):
#         self.test_contract = self._create_test_contract()
#
#     def tearDown(self):
#         self._delete_test_contract()
#
#     def test_query(self):
#         client = Client(contract_schema)
#         executed = client.execute('''{
#   contract {
# 		pageInfo {
#       hasNextPage
#       startCursor
#     }
#     totalCount
#     edgeCount
#     edges {
#       node {
#         amountNotified
#         amountRectified
#         amountDue
#         paymentDueDate
#         status
#         paymentReference
#         jsonExt
#         dateCreated
#         dateUpdated
#         userCreated
#         userUpdated
#         contractFrom
#         contractTo
#       }
#     }
#   }''')
#         assert executed == {
#             'data': {
#                 'hey': 'hello!'
#             }
#         }
#
#     def _create_test_contract(self, custom_properties={}):
#         return create_test_contract(custom_properties)
#
#     def _delete_test_contract(self):
#         Contract.objects.delete(self.test_contract)
#
