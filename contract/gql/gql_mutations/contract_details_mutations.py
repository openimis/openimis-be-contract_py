from core.gql.gql_mutations import DeleteInputType
from core.gql.gql_mutations.base_mutation import BaseMutation, BaseDeleteMutation, \
    BaseHistoryModelCreateMutationMixin, BaseHistoryModelUpdateMutationMixin, \
    BaseHistoryModelDeleteMutationMixin
from .mutations import ContractDetailsFromPHInsureeMutationMixin
from contract.gql.gql_mutations import ContractDetailsCreateInputType, ContractDetailsUpdateInputType, \
    ContractDetailsCreateFromInsureeInputType
from contract.models import ContractDetails, ContractDetailsMutation


class CreateContractDetailsMutation(BaseHistoryModelCreateMutationMixin, BaseMutation):
    _mutation_class = "ContractDetailsMutation"
    _mutation_module = "contract"
    _model = ContractDetails

    @classmethod
    def _mutate(cls, user, **data):
        client_mutation_id = data.get("client_mutation_id")
        if "client_mutation_id" in data:
            data.pop('client_mutation_id')
        if "client_mutation_label" in data:
            data.pop('client_mutation_label')
        contract_detail = cls.create_object(user=user, object_data=data)
        ContractDetailsMutation.object_mutated(user, client_mutation_id=client_mutation_id, contract_detail=contract_detail)
        return None

    class Input(ContractDetailsCreateInputType):
        pass


class UpdateContractDetailsMutation(BaseHistoryModelUpdateMutationMixin, BaseMutation):
    _mutation_class = "ContractDetailsMutation"
    _mutation_module = "contract"
    _model = ContractDetails

    class Input(ContractDetailsUpdateInputType):
        pass


class DeleteContractDetailsMutation(BaseHistoryModelDeleteMutationMixin, BaseDeleteMutation):
    _mutation_class = "ContractDetailsMutation"
    _mutation_module = "contract"
    _model = ContractDetails

    class Input(DeleteInputType):
        pass


class CreateContractDetailByPolicyHolderInsureeMutation(ContractDetailsFromPHInsureeMutationMixin, BaseMutation):
    _mutation_class = "CreateContractDetailByPolicyHolderInsureetMutation"
    _mutation_module = "contract"
    _model = ContractDetails

    class Input(ContractDetailsCreateFromInsureeInputType):
        pass