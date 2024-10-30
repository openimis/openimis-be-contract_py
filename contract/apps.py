from django.apps import AppConfig

MODULE_NAME = "contract"


DEFAULT_CFG = {
    "gql_query_contract_perms": ["152101"],
    "gql_query_contract_admins_perms": [],
    "gql_mutation_create_contract_perms": ["152102"],
    "gql_mutation_update_contract_perms": ["152103"],
    "gql_mutation_delete_contract_perms": ["152104"],
    "gql_mutation_renew_contract_perms": ["152106"],
    "gql_mutation_submit_contract_perms": ["152107"],
    "gql_mutation_approve_ask_for_change_contract_perms": ["152108"],
    "gql_mutation_amend_contract_perms": ["152109"],
    "gql_query_payment_perms": ["101401"],
    "gql_mutation_create_payments_perms": ["101402"],
    "gql_mutation_update_payments_perms": ["101403"],
    "gql_mutation_delete_payments_perms": ["101404"],
    "gql_mutation_approve_payments_perms": ["101408"],
    # OFS-259: Support the policyholder portal perms on Contract
    "gql_query_contract_policyholder_portal_perms": ["154201"],
    "gql_mutation_create_contract_policyholder_portal_perms": ["154202"],
    "gql_mutation_update_contract_policyholder_portal_perms": ["154203"],
    "gql_mutation_submit_contract_policyholder_portal_perms": ["154207"],
    "gql_mutation_amend_contract_policyholder_portal_perms": ["154209"],
    "gql_invoice_create_perms": ["155102"],
}


class ContractConfig(AppConfig):
    name = MODULE_NAME
    gql_query_contract_perms = []
    gql_query_contract_admins_perms = []
    gql_mutation_create_contract_perms = []
    gql_mutation_update_contract_perms = []
    gql_mutation_delete_contract_perms = []
    gql_mutation_renew_contract_perms = []
    gql_mutation_submit_contract_perms = []
    gql_mutation_approve_ask_for_change_contract_perms = []
    gql_mutation_amend_contract_perms = []
    gql_mutation_create_payments_perms = []
    gql_mutation_update_payments_perms = []
    gql_mutation_delete_payments_perms = []
    gql_mutation_approve_payments_perms = []
    # OFS-259: Support the policyholder portal perms on Contract
    gql_query_contract_policyholder_portal_perms = []
    gql_mutation_create_contract_policyholder_portal_perms = []
    gql_mutation_update_contract_policyholder_portal_perms = []
    gql_mutation_submit_contract_policyholder_portal_perms = []
    gql_mutation_amend_contract_policyholder_portal_perms = []
    gql_invoice_create_perms = []

    def __load_config(self, cfg):
        for field in cfg:
            if hasattr(ContractConfig, field):
                setattr(ContractConfig, field, cfg[field])

    def ready(self):
        from core.models import ModuleConfiguration

        cfg = ModuleConfiguration.get_or_default(MODULE_NAME, DEFAULT_CFG)
        self.__load_config(cfg)
