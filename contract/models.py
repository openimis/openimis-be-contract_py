import uuid

from contribution_plan.models import ContributionPlanBundle, ContributionPlan
from django.conf import settings
from django.db import models
from core import models as core_models, fields
from graphql import ResolveInfo
from jsonfallback.fields import FallbackJSONField
from policy.models import Policy
from policyholder.models import PolicyHolder, PolicyHolderInsuree


class ContractManager(models.Manager):
    def filter(self, *args, **kwargs):
        keys = [x for x in kwargs if "itemsvc" in x]
        for key in keys:
            new_key = key.replace("itemsvc", self.model.model_prefix)
            kwargs[new_key] = kwargs.pop(key)
        return super(ContractManager, self).filter(*args, **kwargs)


class Contract(core_models.UUIDVersionedModel):
    id = models.AutoField(db_column='ContractId', primary_key=True)
    uuid = models.CharField(db_column='ContractUUID', max_length=36, default=uuid.uuid4, unique=True)
    version = models.IntegerField()

    policy_holder = models.ForeignKey(PolicyHolder, db_column="PolicyHolderUUID",
                                      on_delete=models.deletion.DO_NOTHING)

    amount_notified = models.FloatField(db_column='AmountNotified')
    amount_rectified = models.FloatField(db_column='AmountRectified')
    amount_due = models.FloatField(db_column='AmountDue')

    payment_due_date = fields.DateTimeField(db_column='PaymentDueDate')
    status = models.SmallIntegerField(db_column='Status')
    payment_reference = models.CharField(db_column='PaymentReference', max_length=255)

    json_ext = FallbackJSONField(db_column='Json_ext', blank=True, null=True)

    date_created = fields.DateTimeField(db_column="DateCreated")
    date_updated = fields.DateTimeField(db_column="DateUpdated", null=True)

    user_updated = models.ForeignKey(core_models.User, db_column="UserUpdatedUUID",
                                     related_name="%(class)s_UpdatedUUID", on_delete=models.deletion.DO_NOTHING)
    user_created = models.ForeignKey(core_models.User, db_column="UserCreatedUUID", null=True,
                                     related_name="%(class)s_CreatedUUID", on_delete=models.deletion.DO_NOTHING)

    contract_from = fields.DateTimeField(db_column="ContractFrom")
    contract_to = fields.DateTimeField("ContractTo", null=True)

    objects = ContractManager()

    @classmethod
    def get_queryset(cls, queryset, user):
        queryset = cls.filter_queryset(queryset)
        if isinstance(user, ResolveInfo):
            user = user.context.user
        if settings.ROW_SECURITY and user.is_anonymous:
            return queryset.filter(id=-1)
        if settings.ROW_SECURITY:
            pass
        return queryset

    class Meta:
        db_table = 'tblContract'

    STATUS_REJECTED = 1
    STATUS_ENTERED = 2
    STATUS_SUBMITTED = 4
    STATUS_PROCESSED = 8


class ContractDetailsManager(models.Manager):
    def filter(self, *args, **kwargs):
        keys = [x for x in kwargs if "itemsvc" in x]
        for key in keys:
            new_key = key.replace("itemsvc", self.model.model_prefix)
            kwargs[new_key] = kwargs.pop(key)
        return super(ContractDetailsManager, self).filter(*args, **kwargs)


class ContractDetails(core_models.UUIDVersionedModel):
    id = models.AutoField(db_column='ContractDetailsId', primary_key=True)
    uuid = models.CharField(db_column='ContractDetailsUUID', max_length=36,
                            default=uuid.uuid4, unique=True)

    contract = models.ForeignKey(Contract, db_column="ContractUUID",
                                      on_delete=models.deletion.DO_NOTHING)
    policy_holder_insuree = models.ForeignKey(PolicyHolderInsuree, db_column='PolicyHolderInsureeUUID',
                                              on_delete=models.deletion.DO_NOTHING)
    contribution_plan_bundle = models.ForeignKey(ContributionPlanBundle,
                                                 db_column='ContributionPlanBundleUUID',
                                                 on_delete=models.deletion.DO_NOTHING)

    json_ext = FallbackJSONField(db_column='Json_ext', blank=True, null=True)
    json_param = FallbackJSONField(db_column='Json_param', blank=True, null=True)
    json_param_history = FallbackJSONField(db_column='Json_param_history', blank=True, null=True)

    date_created = fields.DateTimeField(db_column="DateCreated")
    date_updated = fields.DateTimeField(db_column="DateUpdated", null=True)

    user_updated = models.ForeignKey(core_models.User, db_column="UserUpdatedUUID",
                                     related_name="%(class)s_UpdatedUUID", on_delete=models.deletion.DO_NOTHING)
    user_created = models.ForeignKey(core_models.User, db_column="UserCreatedUUID", null=True,
                                     related_name="%(class)s_CreatedUUID", on_delete=models.deletion.DO_NOTHING)

    objects = ContractDetailsManager()

    class Meta:
        db_table = 'tblContractDetails'


class ContractContributionPlanDetailsManager(models.Manager):
    def filter(self, *args, **kwargs):
        keys = [x for x in kwargs if "itemsvc" in x]
        for key in keys:
            new_key = key.replace("itemsvc", self.model.model_prefix)
            kwargs[new_key] = kwargs.pop(key)
        return super(ContractContributionPlanDetailsManager, self).filter(*args, **kwargs)


class ContractContributionPlanDetails(core_models.UUIDVersionedModel):
    id = models.AutoField(db_column='ContractContributionPlanDetailsId', primary_key=True)
    uuid = models.CharField(db_column='ContractContributionPlanDetailsUUID', max_length=36,
                            default=uuid.uuid4, unique=True)

    version = models.IntegerField()
    contribution_plan = models.ForeignKey(ContributionPlan, db_column='ContributionPlanUUID',
                                          on_delete=models.deletion.DO_NOTHING)
    policy = models.ForeignKey(Policy, db_column='PolicyUUID',
                               on_delete=models.deletion.DO_NOTHING)
    contract_details = models.ForeignKey(ContractDetails, db_column='ContractDetailsUUID',
                                         on_delete=models.deletion.DO_NOTHING)

    json_ext = FallbackJSONField(db_column='Json_ext', blank=True, null=True)
    date_created = fields.DateTimeField(db_column="DateCreated")
    date_updated = fields.DateTimeField(db_column="DateUpdated", null=True)

    user_updated = models.ForeignKey(core_models.User, db_column="UserUpdatedUUID",
                                     related_name="%(class)s_UpdatedUUID", on_delete=models.deletion.DO_NOTHING)
    user_created = models.ForeignKey(core_models.User, db_column="UserCreatedUUID", null=True,
                                     related_name="%(class)s_CreatedUUID", on_delete=models.deletion.DO_NOTHING)

    objects = ContractContributionPlanDetailsManager()

    class Meta:
        db_table = 'tblContractContributionPlanDetails'


class ContractMutation(core_models.UUIDModel):
    contract = models.ForeignKey(Contract, models.DO_NOTHING, related_name='mutations')

    mutation = models.ForeignKey(core_models.MutationLog, models.DO_NOTHING, related_name='contract')

    class Meta:
        db_table = "contract_ContractMutation"
