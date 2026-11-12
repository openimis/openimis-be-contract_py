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
from contract.models import Contract, ContractDetails, ContractDetailsMutation
from core.rights_scope import has_model_right
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext as _
from insuree.models import Insuree
from policyholder.models import PolicyHolderInsuree

from .mutations import ContractDetailsFromPHInsureeMutationMixin


def _check_contract_and_insuree(user, contract_id, insuree_id):
    """Refuse a contract line on a contract or for an insuree out of the user's reach.

    The contract must be one the user may read. The insuree must be enrolled with
    the contract's policy holder - the frontend only offers those - or, for a
    contract with no policy holder, be an insuree the user may read.
    """
    contract = Contract.get_queryset(Contract.objects.filter(id=contract_id), user).first()
    if contract is None:
        raise PermissionDenied(_("unauthorized"))
    if contract.policy_holder_id:
        allowed = PolicyHolderInsuree.objects.filter(
            policy_holder_id=contract.policy_holder_id,
            insuree_id=insuree_id,
            is_deleted=False,
        ).exists()
    else:
        allowed = Insuree.get_queryset(Insuree.objects.filter(id=insuree_id), user).exists()
    if not allowed:
        raise PermissionDenied(_("unauthorized"))


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
        _check_contract_and_insuree(user, data.get("contract_id"), data.get("insuree_id"))

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
        if data.get("contract_id") or data.get("insuree_id"):
            # Moving a line to another contract or insuree is checked like a
            # creation; the line itself is looked up through its scoped queryset.
            current = cls._target_queryset(user).filter(id=data.get("id")).first()
            if current is not None:
                _check_contract_and_insuree(
                    user,
                    data.get("contract_id") or current.contract_id,
                    data.get("insuree_id") or current.insuree_id,
                )

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
