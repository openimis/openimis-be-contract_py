from contribution.models import Premium
from contribution_plan.models import ContributionPlan, ContributionPlanBundle
from core import fields
from core import models as core_models
from django.conf import settings
from django.db import models
from graphql import ResolveInfo
from insuree.models import Insuree
from policy.models import Policy
from policyholder.models import PolicyHolder


class ContractManager(models.Manager):
    def filter(self, *args, **kwargs):
        keys = [x for x in kwargs if "itemsvc" in x]
        for key in keys:
            new_key = key.replace("itemsvc", self.model.model_prefix)
            kwargs[new_key] = kwargs.pop(key)
        return super(ContractManager, self).filter(*args, **kwargs)


class Contract(core_models.HistoryBusinessModel):
    # A contract is exactly as visible as the policy holder it is written for:
    # that holder owns the location this data hangs off. Nullable on purpose --
    # a contract with no holder has nothing to narrow it by, so it stays
    # visible, the same way a null location does.
    # TODO: `policy_holder` should become a GenericForeignKey (`subject`), so a
    # contract can be held by whatever the deployment contracts with -- a
    # PolicyHolder today, an Individual or a Group tomorrow -- instead of one
    # hardcoded model. At that point this becomes `GenericScope("subject")`,
    # which scopes through whichever subject type is stored and already keeps
    # subject-less rows visible, so the rule below does not change meaning.
    row_scope = core_models.ParentScope("policy_holder", allow_null=True)

    code = models.CharField(db_column="Code", max_length=64, null=False)
    policy_holder = models.ForeignKey(
        PolicyHolder,
        db_column="PolicyHolderUUID",
        on_delete=models.deletion.DO_NOTHING,
        blank=True,
        null=True,
    )
    amount_notified = models.FloatField(
        db_column="AmountNotified", blank=True, null=True
    )
    amount_rectified = models.FloatField(
        db_column="AmountRectified", blank=True, null=True
    )
    amount_due = models.FloatField(db_column="AmountDue", blank=True, null=True)
    date_approved = fields.DateTimeField(
        db_column="DateApproved", blank=True, null=True
    )
    date_payment_due = fields.DateField(
        db_column="DatePaymentDue", blank=True, null=True
    )
    state = models.SmallIntegerField(db_column="State", blank=True, null=True)
    payment_reference = models.CharField(
        db_column="PaymentReference", max_length=255, blank=True, null=True
    )
    amendment = models.IntegerField(
        db_column="Amendment", blank=False, null=False, default=0
    )

    objects = ContractManager()

    @property
    def amount(self):
        amount = 0
        if self.state in [1, 2]:
            amount = self.amount_notified
        elif self.state in [4, 11, 3]:
            amount = self.amount_rectified
        elif self.state in [5, 6, 7, 8, 9, 10]:
            amount = self.amount_due
        else:
            amount = self.amount_due
        return amount

    @classmethod
    def get_queryset(cls, queryset, user):
        # Validity first, then `row_scope` via the mixin: the row security
        # itself is declared above, not restated here.
        return super().get_queryset(cls.filter_queryset(queryset), user)

    class Meta:
        db_table = "tblContract"

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
    STATE_COUNTER = 11

    def contract_business_validity(self, prefix=''):
        return [
            models.Q(**{f'{prefix}date_valid_from__lte': self.date_valid_to}),
            models.Q(**{
                f'{prefix}date_valid_to__isnull': True
            }) | models.Q(**{
                f'{prefix}date_valid_to__gte': self.date_valid_from
            }),
        ]


    @classmethod
    def get_rights(cls, action):
        """
        Les droits régissant une action sur cette entité, pour GraphQL, REST et FHIR.

        Ne redéclare rien : la table des droits est `contract.apps.DJANGO_PERMS`, par
        entité puis par action, et `configured_perms` y lit la valeur *configurée* -
        celle que ModuleConfiguration a pu surcharger - et non le défaut déclaré. Ce
        modèle n'est que le point d'accès, comme `get_queryset` l'est pour les lignes.
        """
        from contract.apps import configured_perms

        return configured_perms("contract", action)


class ContractDetailsManager(models.Manager):
    def filter(self, *args, **kwargs):
        keys = [x for x in kwargs if "itemsvc" in x]
        for key in keys:
            new_key = key.replace("itemsvc", self.model.model_prefix)
            kwargs[new_key] = kwargs.pop(key)
        return super(ContractDetailsManager, self).filter(*args, **kwargs)


class ContractDetails(core_models.HistoryModel):
    # A line of a contract is not an object anyone holds rights on separately: editing
    # one is editing that contract. `scope_parent` says which of the three foreign
    # keys below is the owner, so `core.rights_scope` can find the contract's rights
    # instead of this model needing its own. It has to be declared - insuree and
    # contribution_plan_bundle are just as much foreign keys, and neither governs who
    # may change a contract line.
    scope_parent = "contract"

    contract = models.ForeignKey(
        Contract, db_column="ContractUUID", on_delete=models.deletion.CASCADE
    )
    insuree = models.ForeignKey(
        Insuree, db_column="InsureeID", on_delete=models.deletion.DO_NOTHING
    )
    contribution_plan_bundle = models.ForeignKey(
        ContributionPlanBundle,
        db_column="ContributionPlanBundleUUID",
        on_delete=models.deletion.DO_NOTHING,
    )

    json_param = models.JSONField(db_column="Json_param", blank=True, null=True)

    objects = ContractDetailsManager()

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
        db_table = "tblContractDetails"


class ContractContributionPlanDetailsManager(models.Manager):
    def filter(self, *args, **kwargs):
        keys = [x for x in kwargs if "itemsvc" in x]
        for key in keys:
            new_key = key.replace("itemsvc", self.model.model_prefix)
            kwargs[new_key] = kwargs.pop(key)
        return super(ContractContributionPlanDetailsManager, self).filter(
            *args, **kwargs
        )


class ContractContributionPlanDetails(core_models.HistoryBusinessModel):
    contribution_plan = models.ForeignKey(
        ContributionPlan,
        db_column="ContributionPlanUUID",
        on_delete=models.deletion.DO_NOTHING,
    )
    policy = models.ForeignKey(
        Policy,
        db_column="PolicyID",
        on_delete=models.deletion.DO_NOTHING,
        blank=True,
        null=True,
    )
    contract_details = models.ForeignKey(
        ContractDetails,
        db_column="ContractDetailsUUID",
        on_delete=models.deletion.CASCADE,
    )
    contribution = models.ForeignKey(
        Premium,
        db_column="ContributionId",
        related_name="contract_contribution_plan_details",
        on_delete=models.deletion.DO_NOTHING,
        blank=True,
        null=True,
    )
    amount = models.DecimalField(
        db_column='Amount',
        max_digits=18, decimal_places=2, blank=True, null=True)

    objects = ContractContributionPlanDetailsManager()

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
        db_table = "tblContractContributionPlanDetails"


class ContractMutation(core_models.UUIDModel, core_models.ObjectMutation):
    row_scope = core_models.ParentScope("contract")

    contract = models.ForeignKey(Contract, models.DO_NOTHING, related_name="mutations")
    mutation = models.ForeignKey(
        core_models.MutationLog, models.DO_NOTHING, related_name="contracts"
    )

    class Meta:
        managed = True
        db_table = "contract_contractMutation"


class ContractDetailsMutation(core_models.UUIDModel, core_models.ObjectMutation):
    row_scope = core_models.ParentScope("contract_detail")

    contract_detail = models.ForeignKey(
        ContractDetails, models.DO_NOTHING, related_name="mutations"
    )
    mutation = models.ForeignKey(
        core_models.MutationLog, models.DO_NOTHING, related_name="contract_details"
    )

    class Meta:
        managed = True
        db_table = "contract_contractDetailsMutation"
