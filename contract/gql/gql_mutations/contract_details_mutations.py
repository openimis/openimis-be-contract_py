from core.gql.gql_mutations import DeleteInputType
from core.gql.gql_mutations.base_mutation import (
    BaseDeleteMutation,
    BaseHistoryModelCreateMutationMixin,
    BaseHistoryModelDeleteMutationMixin,
    BaseHistoryModelUpdateMutationMixin,
    BaseMutation,
)

from contract.gql.gql_mutations.input_types import (
    ContractDetailsCreateFromInsureeInputType,
    ContractDetailsCreateInputType,
    ContractDetailsUpdateInputType,
)
from contract.models import ContractDetails, ContractDetailsMutation
from core.rights_scope import has_model_right
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext as _

from .mutations import ContractDetailsFromPHInsureeMutationMixin


class CreateContractDetailsMutation(BaseHistoryModelCreateMutationMixin, BaseMutation):
    _mutation_class = "ContractDetailsMutation"
    _mutation_module = "contract"
    _model = ContractDetails

    @classmethod
    def _validate_mutation(cls, user, **data):
        super()._validate_mutation(user, **data)
        # ContractDetails declares scope_parent = "contract", so this resolves to the
        # contract's own create right. Until now these three mutations overrode
        # nothing, which left them on the base mixin's check - authentication only -
        # so any logged-in user could add, edit or remove the lines of any contract.
        if not has_model_right(user, cls._model, "create"):
            raise PermissionDenied(_("unauthorized"))

    @classmethod
    def _mutate(cls, user, **data):
        client_mutation_id = data.get("client_mutation_id")
        if "client_mutation_id" in data:
            data.pop("client_mutation_id")
        if "client_mutation_label" in data:
            data.pop("client_mutation_label")
        contract_detail = cls.create_object(user=user, object_data=data)
        ContractDetailsMutation.object_mutated(
            user, client_mutation_id=client_mutation_id, contract_detail=contract_detail
        )
        return None

    class Input(ContractDetailsCreateInputType):
        pass


class UpdateContractDetailsMutation(BaseHistoryModelUpdateMutationMixin, BaseMutation):
    _mutation_class = "ContractDetailsMutation"
    _mutation_module = "contract"
    _model = ContractDetails

    @classmethod
    def _validate_mutation(cls, user, **data):
        super()._validate_mutation(user, **data)
        # ContractDetails declares scope_parent = "contract", so this resolves to the
        # contract's own update right. Until now these three mutations overrode
        # nothing, which left them on the base mixin's check - authentication only -
        # so any logged-in user could add, edit or remove the lines of any contract.
        if not has_model_right(user, cls._model, "update"):
            raise PermissionDenied(_("unauthorized"))

    class Input(ContractDetailsUpdateInputType):
        pass


class DeleteContractDetailsMutation(
    BaseHistoryModelDeleteMutationMixin, BaseDeleteMutation
):
    _mutation_class = "ContractDetailsMutation"
    _mutation_module = "contract"
    _model = ContractDetails

    @classmethod
    def _validate_mutation(cls, user, **data):
        super()._validate_mutation(user, **data)
        # ContractDetails declares scope_parent = "contract", so this resolves to the
        # contract's own delete right. Until now these three mutations overrode
        # nothing, which left them on the base mixin's check - authentication only -
        # so any logged-in user could add, edit or remove the lines of any contract.
        if not has_model_right(user, cls._model, "delete"):
            raise PermissionDenied(_("unauthorized"))

    class Input(DeleteInputType):
        pass


class CreateContractDetailByPolicyHolderInsureeMutation(
    ContractDetailsFromPHInsureeMutationMixin, BaseMutation
):
    _mutation_class = "CreateContractDetailByPolicyHolderInsureetMutation"
    _mutation_module = "contract"
    _model = ContractDetails

    class Input(ContractDetailsCreateFromInsureeInputType):
        pass
