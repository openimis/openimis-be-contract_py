import uuid

from contribution_plan.models import ContributionPlanBundle, ContributionPlan
from django.conf import settings
from django.db import models
from core import models as core_models, fields
from graphql import ResolveInfo
from jsonfallback.fields import FallbackJSONField
from policy.models import Policy
from contribution.models import Premium
from policyholder.models import PolicyHolder
from insuree.models import Insuree


class ContractManager(models.Manager):
    def filter(self, *args, **kwargs):
        keys = [x for x in kwargs if "itemsvc" in x]
        for key in keys:
            new_key = key.replace("itemsvc", self.model.model_prefix)
            kwargs[new_key] = kwargs.pop(key)
        return super(ContractManager, self).filter(*args, **kwargs)


class Contract(core_models.HistoryBusinessModel):
    code = models.CharField(db_column='Code', max_length=64, null=False)
    policy_holder = models.ForeignKey(PolicyHolder, db_column="PolicyHolderUUID",
                                      on_delete=models.deletion.DO_NOTHING, blank=True, null=True)
    amount_notified = models.FloatField(db_column='AmountNotified', blank=True, null=True)
    amount_rectified = models.FloatField(db_column='AmountRectified', blank=True, null=True)
    amount_due = models.FloatField(db_column='AmountDue', blank=True, null=True)
    date_approved = fields.DateTimeField(db_column='DateApproved', blank=True, null=True)
    date_payment_due = fields.DateField(db_column='DatePaymentDue', blank=True, null=True)
    state = models.SmallIntegerField(db_column='State', blank=True, null=True)
    payment_reference = models.CharField(db_column='PaymentReference', max_length=255, blank=True, null=True)
    amendment = models.IntegerField(db_column='Amendment', blank=False, null=False, default=0)

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

    STATE_REQUEST_FOR_INFORMATION = 1
    STATE_DRAFT = 2
    STATE_OFFER = 3
    STATE_NEGOTIABLE = 4
    STATE_EXECUTABLE = 5
    STATE_ADDENDUM = 6
    STATE_EFFECTIVE = 7
    STATE_EXECUTED = 8
    STATE_DISPUTED = 9
    STATE_TERMINATED = 10


class ContractDetailsManager(models.Manager):
    def filter(self, *args, **kwargs):
        keys = [x for x in kwargs if "itemsvc" in x]
        for key in keys:
            new_key = key.replace("itemsvc", self.model.model_prefix)
            kwargs[new_key] = kwargs.pop(key)
        return super(ContractDetailsManager, self).filter(*args, **kwargs)


class ContractDetails(core_models.HistoryModel):
    contract = models.ForeignKey(Contract, db_column="ContractUUID",
                                      on_delete=models.deletion.DO_NOTHING)
    insuree = models.ForeignKey(Insuree, db_column='InsureeID',
                                              on_delete=models.deletion.DO_NOTHING)
    contribution_plan_bundle = models.ForeignKey(ContributionPlanBundle,
                                                 db_column='ContributionPlanBundleUUID',
                                                 on_delete=models.deletion.DO_NOTHING)

    json_param = FallbackJSONField(db_column='Json_param', blank=True, null=True)

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


class ContractContributionPlanDetails(core_models.HistoryModel):
    contribution_plan = models.ForeignKey(ContributionPlan, db_column='ContributionPlanUUID',
                                          on_delete=models.deletion.DO_NOTHING)
    policy = models.ForeignKey(Policy, db_column='PolicyID',
                               on_delete=models.deletion.DO_NOTHING)
    contract_details = models.ForeignKey(ContractDetails, db_column='ContractDetailsUUID',
                                         on_delete=models.deletion.DO_NOTHING)
    contribution = models.ForeignKey(Premium, db_column='ContributionId',
                                         on_delete=models.deletion.DO_NOTHING, blank=True, null=True)

    objects = ContractContributionPlanDetailsManager()

    class Meta:
        db_table = 'tblContractContributionPlanDetails'