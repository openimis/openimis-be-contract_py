# openIMIS Backend Contract reference module
This repository holds the files of the openIMIS Backend Contract reference module.
It is dedicated to be deployed as a module of [openimis-be_py](https://github.com/openimis/openimis-be_py).

## ORM mapping:
* tblContract > Contract
* tblContractDetails > ContractDetails
* tblContractContributionPlanDetails > ContractContributionPlanDetails

## Listened Django Signals
- post_save of Payment: handles service activate_contracted_policies - only when payment 
is related to the contract/contracts. (it is verified by this post save)
Another payments are omitted in processing.

## GraphQl Queries
* contract 
* contractDetails
* contractContributionPlanDetails

## GraphQL Mutations - each mutation emits default signals and return standard error lists (cfr. openimis-be-core_py)
* createContract
* updateContract
* deleteContract
* submitContract
* approveContract
* approveBulkContract (works with Celery)
* counterContract
* amendContract
* renewContract
* createContractDetails
* updateContractDetails
* deleteContractDetails
* createContractDetailsByPhInsuree

## Services
- Contract
  - create
  - update
  - submit
  - approve
  - amend
  - renew
  - delete
  - get_negative_amount_amendment
  - terminate 
- ContractDetails
  - update_from_ph_insuree
  - ph_insuree_to_contract_details  
- ContractContributionPlanDetails - CRUD services, replace
  - create_ccpd (ccpd - acronym of contrac contribution plan details)
  - contract_valuation
  - create_contribution
- PaymentService
  - create
  - collect_payment_details

## Configuration options (can be changed via core.ModuleConfiguration)
* gql_query_contract_perms: required rights to call createContract GraphQL Query (default: ["152101"])
* gql_query_contract_admins_perms: required rights to call contribution_plan_bundle_admin GraphQL Query (default: [])

* gql_mutation_create_contract_perms: required rights to call createContract, createContractDetails GraphQL Mutations (default: ["152102"])
* gql_mutation_update_contract_perms: required rights to call updateContract, updateContractDetails GraphQL Mutations (default: ["152103"])
* gql_mutation_delete_contract_perms: required rights to call deleteContract, deleteContractDetails GraphQL Mutations (default: ["152104"])
* gql_mutation_renew_contract_perms: required rights to call renewContract GraphQL Mutation (default: ["152106"])
* gql_mutation_submit_contract_perms: required rights to call submitContract GraphQL Mutation (default: ["152107"])
* gql_mutation_approve_ask_for_change_contract_perms: required rights to call approveContract, approveBulkContract and counterContract GraphQL Mutations (default: ["152108"])
* gql_mutation_amend_contract_perms: required rights to call amendContract GraphQL Mutation (default: ["152109"])
