from django.apps import AppConfig

from core.rights_declaration import RightsDeclaration

MODULE_NAME = "contract"


# Droits, par entité puis par action. Même structure que `core.apps.DJANGO_PERMS`.
#
# Deux entités partagent volontairement les identifiants d'un autre module, parce qu'il
# s'agit de la même action sur le même objet : les paiements d'un contrat prennent les
# droits du module payment (1014xx), et la création d'une facture celui du module
# invoice (155102). Ce n'est pas une collision, c'est une réutilisation.
DJANGO_PERMS = {
    "contract": {
        "query": ("contract.view_contract", 152101),
        "create": ("contract.add_contract", 152102),
        "update": ("contract.change_contract", 152103),
        "delete": ("contract.delete_contract", 152104),
        "queryAdmins": ("contract.view_contract_admin", 152105),
        "renew": ("contract.renew_contract", 152106),
        "submit": ("contract.submit_contract", 152107),
        "approveAskForChange": ("contract.approve_ask_for_change_contract", 152108),
        "amend": ("contract.amend_contract", 152109),
    },
    "contractPayment": {
        "query": ("contract.view_payment", 101401),
        "create": ("contract.add_payment", 101402),
        "update": ("contract.change_payment", 101403),
        "delete": ("contract.delete_payment", 101404),
        "approve": ("contract.approve_payment", 101408),
    },
    "contractPortal": {
        "query": ("contract.view_contract_portal", 154201),
        "create": ("contract.add_contract_portal", 154202),
        "update": ("contract.change_contract_portal", 154203),
        "submit": ("contract.submit_contract_portal", 154207),
        "amend": ("contract.amend_contract_portal", 154209),
    },
    "contractInvoice": {
        "create": ("contract.add_contract_invoice", 155102),
    },
}

_PERM_CFG = {
    "gql_query_contract_perms": ("contract", "query"),
    "gql_query_contract_admins_perms": ("contract", "queryAdmins"),
    "gql_mutation_create_contract_perms": ("contract", "create"),
    "gql_mutation_update_contract_perms": ("contract", "update"),
    "gql_mutation_delete_contract_perms": ("contract", "delete"),
    "gql_mutation_renew_contract_perms": ("contract", "renew"),
    "gql_mutation_submit_contract_perms": ("contract", "submit"),
    "gql_mutation_approve_ask_for_change_contract_perms": ("contract", "approveAskForChange"),
    "gql_mutation_amend_contract_perms": ("contract", "amend"),
    "gql_query_payment_perms": ("contractPayment", "query"),
    "gql_mutation_create_payments_perms": ("contractPayment", "create"),
    "gql_mutation_update_payments_perms": ("contractPayment", "update"),
    "gql_mutation_delete_payments_perms": ("contractPayment", "delete"),
    "gql_mutation_approve_payments_perms": ("contractPayment", "approve"),
    "gql_query_contract_policyholder_portal_perms": ("contractPortal", "query"),
    "gql_mutation_create_contract_policyholder_portal_perms": ("contractPortal", "create"),
    "gql_mutation_update_contract_policyholder_portal_perms": ("contractPortal", "update"),
    "gql_mutation_submit_contract_policyholder_portal_perms": ("contractPortal", "submit"),
    "gql_mutation_amend_contract_policyholder_portal_perms": ("contractPortal", "amend"),
    "gql_invoice_create_perms": ("contractInvoice", "create"),
}

RIGHTS = RightsDeclaration(MODULE_NAME, DJANGO_PERMS, _PERM_CFG)

perms = RIGHTS.perms
django_perms = RIGHTS.django_perm_names
configured_perms = RIGHTS.configured
require = RIGHTS.require


DEFAULT_CFG = {
    # 152105: the free 05 slot in this entity's block (01 query, 02 create,
    # 03 update, 04 delete, 06 replace). Nothing reads this constant yet - the id
    # is minted so that wiring it up later grants a real right rather than [],
    # which `has_perms` treats as granted to everyone.
    # OFS-259: Support the policyholder portal perms on Contract
}


class ContractConfig(AppConfig):
    name = MODULE_NAME
    # Rights: constants derived from DJANGO_PERMS, no longer overridable. They go
    # neither through DEFAULT_CFG nor through ready().
    gql_query_contract_perms = RIGHTS.perms("contract", "query")
    gql_query_contract_admins_perms = RIGHTS.perms("contract", "queryAdmins")
    gql_mutation_create_contract_perms = RIGHTS.perms("contract", "create")
    gql_mutation_update_contract_perms = RIGHTS.perms("contract", "update")
    gql_mutation_delete_contract_perms = RIGHTS.perms("contract", "delete")
    gql_mutation_renew_contract_perms = RIGHTS.perms("contract", "renew")
    gql_mutation_submit_contract_perms = RIGHTS.perms("contract", "submit")
    gql_mutation_approve_ask_for_change_contract_perms = RIGHTS.perms("contract", "approveAskForChange")
    gql_mutation_amend_contract_perms = RIGHTS.perms("contract", "amend")
    # `__load_config` n'affecte que les cles de config ayant deja un attribut ici :
    # celle-ci n'en avait pas, donc elle n'etait jamais chargee et sa lecture levait
    # AttributeError - le droit etait declare mais inapplicable. Rien ne la lit
    # aujourd'hui, ce qui explique que personne ne s'en soit apercu.
    gql_query_payment_perms = RIGHTS.perms("contractPayment", "query")
    gql_mutation_create_payments_perms = RIGHTS.perms("contractPayment", "create")
    gql_mutation_update_payments_perms = RIGHTS.perms("contractPayment", "update")
    gql_mutation_delete_payments_perms = RIGHTS.perms("contractPayment", "delete")
    gql_mutation_approve_payments_perms = RIGHTS.perms("contractPayment", "approve")
    # OFS-259: Support the policyholder portal perms on Contract
    gql_query_contract_policyholder_portal_perms = RIGHTS.perms("contractPortal", "query")
    gql_mutation_create_contract_policyholder_portal_perms = RIGHTS.perms("contractPortal", "create")
    gql_mutation_update_contract_policyholder_portal_perms = RIGHTS.perms("contractPortal", "update")
    gql_mutation_submit_contract_policyholder_portal_perms = RIGHTS.perms("contractPortal", "submit")
    gql_mutation_amend_contract_policyholder_portal_perms = RIGHTS.perms("contractPortal", "amend")
    gql_invoice_create_perms = RIGHTS.perms("contractInvoice", "create")
    def __load_config(self, cfg):
        for field in cfg:
            if hasattr(ContractConfig, field):
                setattr(ContractConfig, field, cfg[field])

    def ready(self):
        from core.models import ModuleConfiguration

        cfg = ModuleConfiguration.get_or_default(MODULE_NAME, DEFAULT_CFG)
        self.__load_config(cfg)

    def set_dataloaders(self, dataloaders):
        from contract.dataloaders import (
            ContractDetailsByContractLoader,
            ContributionPlanDetailsByContractLoader,
        )

        dataloaders["contract_details_by_contract"] = ContractDetailsByContractLoader()
        dataloaders["contract_contribution_plan_details_by_contract"] = (
            ContributionPlanDetailsByContractLoader()
        )
