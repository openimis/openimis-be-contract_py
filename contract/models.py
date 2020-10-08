import uuid

from contribution_plan.models import ContributionPlanBundle, ContributionPlan
from django.db import models
from core import models as core_models, fields
from jsonfallback.fields import FallbackJSONField
from policy.models import Policy
from policyholder.models import PolicyHolder, PolicyHolderInsuree


class Contract(core_models.UUIDVersionedModel):
    id = models.AutoField(db_column='ContractId', primary_key=True)
    uuid = models.CharField(db_column='ContractUUID', max_length=24, default=uuid.uuid4, unique=True)
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
    date_updated = fields.DateTimeField(db_column="DateUpdated")

    user_updated = models.ForeignKey(core_models.InteractiveUser, db_column="UserUpdatedUUID",
                                     related_name="%(class)s_UpdatedUUID", on_delete=models.deletion.DO_NOTHING)
    user_created = models.ForeignKey(core_models.InteractiveUser, db_column="UserCreatedUUID",
                                     related_name="%(class)s_CreatedUUID", on_delete=models.deletion.DO_NOTHING)

    contract_from = fields.DateTimeField(db_column="ContractFrom")
    contract_to = fields.DateTimeField("ContractTo")

    class Meta:
        db_table = 'tblContract'


class ContractDetailsManager(models.Manager):
    def filter(self, *args, **kwargs):
        keys = [x for x in kwargs if "itemsvc" in x]
        for key in keys:
            new_key = key.replace("itemsvc", self.model.model_prefix)
            kwargs[new_key] = kwargs.pop(key)
        return super(ContractDetailsManager, self).filter(*args, **kwargs)


class ContractDetails(core_models.UUIDVersionedModel):
    id = models.AutoField(db_column='ContractDetailsId', primary_key=True)
    uuid = models.CharField(db_column='ContractDetailsUUID', max_length=24,
                            default=uuid.uuid4, unique=True)

    contract_uuid = models.ForeignKey(Contract, db_column="ContractUUID",
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
    date_updated = fields.DateTimeField(db_column="DateUpdated")

    user_updated = models.ForeignKey(core_models.InteractiveUser, db_column="UserUpdatedUUID",
                                     related_name="%(class)s_UpdatedUUID", on_delete=models.deletion.DO_NOTHING)
    user_created = models.ForeignKey(core_models.InteractiveUser, db_column="UserCreatedUUID",
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


class ContractContributionPlanDetails(models.Model):
    id = models.AutoField(db_column='ContractContributionPlanDetailsId', primary_key=True)
    uuid = models.CharField(db_column='ContractContributionPlanDetailsUUID', max_length=24,
                            default=uuid.uuid4, unique=True)

    version = models.IntegerField()
    contribution_plan = models.ForeignKey(ContributionPlan, db_column='ContributionPlanUUID',
                                          on_delete=models.deletion.DO_NOTHING)
    policy = models.ForeignKey(Policy, db_column='PolicyUUID',
                               on_delete=models.deletion.DO_NOTHING)
    contract_details = models.ForeignKey(ContractDetails, db_column='ContractDetaulsUUID',
                                         on_delete=models.deletion.DO_NOTHING)

    json_ext = FallbackJSONField(db_column='Json_ext', blank=True, null=True)
    date_created = fields.DateTimeField(db_column="DateCreated")
    date_updated = fields.DateTimeField(db_column="DateUpdated")

    user_updated = models.ForeignKey(core_models.InteractiveUser, db_column="UserUpdatedUUID",
                                     related_name="%(class)s_UpdatedUUID", on_delete=models.deletion.DO_NOTHING)
    user_created = models.ForeignKey(core_models.InteractiveUser, db_column="UserCreatedUUID",
                                     related_name="%(class)s_CreatedUUID", on_delete=models.deletion.DO_NOTHING)

    objects = ContractContributionPlanDetailsManager()

    class Meta:
        db_table = 'tblContractContributionPlanDetails'
