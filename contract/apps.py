from django.apps import AppConfig


MODULE_NAME = "contract"


DEFAULT_CFG = {
    "gql_query_contract_perms": ["152101"],
    "gql_query_contract_admins_perms": [],
    "gql_mutation_create_contract_perms": ["152102"],
    "gql_mutation_update_contract_perms": ["152103"],
    "gql_mutation_approve_ask_for_change_contract_perms": ["152108"],
}


class ContractConfig(AppConfig):
    name = MODULE_NAME

    gql_query_contract_perms = []
    gql_query_contract_admins_perms = []
    gql_mutation_create_contract_perms = []
    gql_mutation_update_contract_perms = []
    gql_mutation_approve_ask_for_change_contract_perms = []

    def _configure_permissions(selfself, cfg):
        ContractConfig.gql_query_contract_perms = cfg[
            "gql_query_contract_perms"]
        ContractConfig.gql_query_contract_admins_perms = cfg[
            "gql_query_contract_admins_perms"
        ]
        ContractConfig.gql_mutation_create_contract_perms = cfg[
            "gql_mutation_create_contract_perms"]
        ContractConfig.gql_mutation_update_contract_perms = cfg[
            "gql_mutation_update_contract_perms"
        ]
        ContractConfig.gql_mutation_approve_ask_for_change_contract_perms = cfg[
            "gql_mutation_approve_ask_for_change_contract_perms"
        ]

    def ready(self):
        from core.models import ModuleConfiguration
        cfg = ModuleConfiguration.get_or_default(MODULE_NAME, DEFAULT_CFG)
        self._configure_permissions(cfg)