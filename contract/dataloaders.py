from collections import defaultdict

from promise import Promise
from promise.dataloader import DataLoader

from contract.models import ContractDetails, ContractContributionPlanDetails


class ContractDetailsByContractLoader(DataLoader):
    def batch_load_fn(self, contract_ids):
        grouped = defaultdict(list)

        details = (
            ContractDetails.objects
            .filter(contract_id__in=contract_ids, is_deleted=False)
            .select_related("insuree", "contribution_plan_bundle")
            .order_by("id")
        )

        for detail in details:
            grouped[detail.contract_id].append(detail)

        return Promise.resolve([grouped.get(contract_id, []) for contract_id in contract_ids])


class ContributionPlanDetailsByContractLoader(DataLoader):
    def batch_load_fn(self, contract_ids):
        grouped = defaultdict(list)

        rows = (
            ContractContributionPlanDetails.objects
            .filter(contract_details__contract_id__in=contract_ids, is_deleted=False)
            .select_related(
                "contract_details",
                "contract_details__insuree",
                "contract_details__contribution_plan_bundle",
                "contribution_plan",
                "contribution",
                "policy",
            )
            .order_by("id")
        )

        for row in rows:
            grouped[row.contract_details.contract_id].append(row)

        return Promise.resolve([grouped.get(contract_id, []) for contract_id in contract_ids])
