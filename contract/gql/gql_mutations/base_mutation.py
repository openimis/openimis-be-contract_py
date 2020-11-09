from functools import lru_cache

from core import TimeUtils
from core.schema import OpenIMISMutation
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError

from contract.gql.gql_mutations import ObjectNotExistException


class BaseMutation(OpenIMISMutation):
    _mutation_module = "contributionPlanBundle"

    @property
    def _mutation_class(self):
        raise NotImplementedError()

    @property
    def _model(self):
        raise NotImplementedError()

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


class BaseDeleteMutation(BaseMutation):

    class Input:
        pass

    @classmethod
    def async_mutate(cls, user, **data):
        output = []
        for uuid in data["uuids"]:
            deletion_result = super(BaseDeleteMutation, cls)\
                .async_mutate(user, uuid=uuid)
            output += deletion_result
        return output


class BaseSubmissionMutation(BaseMutation):

    class Input:
        pass

    @classmethod
    def async_mutate(cls, user, **data):
        output = []
        for contract_uuid in data["uuids"]:
            submission_result = super(BaseSubmissionMutation, cls).async_mutate(user, contract_uuid=contract_uuid)
            output += submission_result
        return output


class BaseCreateMutationMixin:

    @property
    def _model(self):
        raise NotImplementedError()

    @classmethod
    def _validate_mutation(cls, user, **data):
        if type(user) is AnonymousUser or not user.id:
            raise ValidationError("mutation.authentication_required")

    @classmethod
    def _mutate(cls, user, **data):
        data['user_created'] = user.id_for_audit
        data['date_created'] = TimeUtils.now()

        if "client_mutation_id" in data:
            data.pop('client_mutation_id')
        if "client_mutation_label" in data:
            data.pop('client_mutation_label')

        cls.create_object(data)

    @classmethod
    def create_object(cls, object_data):
        obj = cls._model.objects.create(**object_data)
        obj.save()
        return obj


class BaseUpdateMutationMixin:

    @property
    def _model(self):
        raise NotImplementedError()

    @classmethod
    def _object_not_exist_exception(cls, obj_uuid):
        raise ObjectNotExistException(cls._model, obj_uuid)

    @classmethod
    def _validate_mutation(cls, user, **data):
        if type(user) is AnonymousUser or not user.id:
            raise ValidationError("mutation.authentication_required")

        obj_uuid = data['uuid']
        if cls._model.objects.filter(uuid=data['uuid']).first() is None:
            cls._object_not_exist_exception(obj_uuid=obj_uuid)

    @classmethod
    def _mutate(cls, user, **data):
        if "client_mutation_id" in data:
            data.pop('client_mutation_id')
        if "client_mutation_label" in data:
            data.pop('client_mutation_label')

        data['user_updated'] = user.id_for_audit
        data['date_updated'] = TimeUtils.now()
        updated_object = cls._model.objects.filter(uuid=data['uuid']).first()
        [setattr(updated_object, key, data[key]) for key in data]
        cls.update_object(updated_object)

    @classmethod
    def update_object(cls, object_to_update):
        object_to_update.save_history()
        object_to_update.save()
        return object_to_update


class BaseDeleteMutationMixin:
    @property
    def _model(self):
        raise NotImplementedError()

    @classmethod
    def _object_not_exist_exception(cls, obj_uuid):
        raise ObjectNotExistException(cls._model, obj_uuid)

    @classmethod
    def _validate_mutation(cls, user, **data):
        cls._validate_user(user)

    @classmethod
    def _validate_user(cls, user):
        if type(user) is AnonymousUser or not user.id:
            raise ValidationError("mutation.authentication_required")

    @classmethod
    def _mutate(cls, uuid):
        object_to_delete = cls._model.objects.filter(uuid=uuid).first()

        if object_to_delete is None:
            cls._object_not_exist_exception(uuid)
        else:
            object_to_delete.delete_history()


class BaseSubmitMutationMixin:

        @classmethod
        def _validate_mutation(cls, user, **data):
            if type(user) is AnonymousUser or not user.id:
                raise ValidationError("mutation.authentication_required")

        @classmethod
        def _mutate(cls, user, **data):
            return cls.submit_by_uuid(data['contract_uuid'])

        @classmethod
        def submit_by_uuid(cls, uuid):
            contract = cls._model.objects.filter(uuid=uuid).first()

            if contract is None:
                raise ObjectNotExistException(cls._model, uuid)
            else:
                cls.submit_obj(contract)

        @classmethod
        def submit_obj(cls, obj):
            cls.validate_submission(obj)
            obj.status = obj.STATUS_SUBMITTED
            obj.save_history()

        @classmethod
        def validate_submission(cls, obj):
            errors = []

            if obj.policy_holder is None:
                obj.status = obj.STATUS_REJECTED
                errors.append("Policy Holder not defined")

            if errors:
                raise ValidationError(obj, errors)
            else:
                return True
