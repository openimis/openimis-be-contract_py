import graphene
from .input_types import ContractInputType
from core.schema import OpenIMISMutation, TinyInt


class BaseContractMutation(OpenIMISMutation):
    _mutation_module = "contract"
    _mutation_class = "BaseContractMutation"

    @classmethod
    def async_mutate(cls, user, **data):
        try:
            cls._validate_mutation(user, **data)
            mutation_result = cls._mutate(user, **data)
            return mutation_result
        except Exception as exc:
            return [{
                'message': "Failed to process {} mutation".format(cls._mutation_class),
                'detail': str(exc)}]

    @classmethod
    def _validate_mutation(cls, user, **data):
        raise NotImplementedError()

    @classmethod
    def _mutate(cls, user, **data):
        raise NotImplementedError()

