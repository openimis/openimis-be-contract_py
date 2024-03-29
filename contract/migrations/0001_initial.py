# Generated by Django 3.0.3 on 2020-12-21 13:12

import core.fields
import datetime
import dirtyfields.dirtyfields
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import simple_history.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('policyholder', '0004_auto_20201214_1302'),
        ('contribution_plan', '0004_auto_20201217_0946'),
        ('policy', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Contract',
            fields=[
                ('id', models.UUIDField(db_column='UUID', default=None, editable=False, primary_key=True, serialize=False)),
                ('is_deleted', models.BooleanField(db_column='isDeleted', default=False)),
                ('json_ext', models.JSONField(blank=True, db_column='Json_ext', null=True)),
                ('date_created', models.DateTimeField(db_column='DateCreated', null=True)),
                ('date_updated', models.DateTimeField(db_column='DateUpdated', null=True)),
                ('version', models.IntegerField(default=1)),
                ('date_valid_from', models.DateTimeField(db_column='DateValidFrom', default=datetime.datetime.now)),
                ('date_valid_to', models.DateTimeField(blank=True, db_column='DateValidTo', null=True)),
                ('replacement_uuid', models.UUIDField(db_column='ReplacementUUID', null=True)),
                ('amount_notified', models.FloatField(db_column='AmountNotified')),
                ('amount_rectified', models.FloatField(db_column='AmountRectified')),
                ('amount_due', models.FloatField(db_column='AmountDue')),
                ('date_approved', core.fields.DateTimeField(db_column='DateApproved')),
                ('date_payment_due', core.fields.DateField(db_column='DatePaymentDue')),
                ('state', models.SmallIntegerField(db_column='State')),
                ('payment_reference', models.CharField(db_column='PaymentReference', max_length=255)),
                ('policy_holder', models.ForeignKey(db_column='PolicyHolderUUID', on_delete=django.db.models.deletion.DO_NOTHING, to='policyholder.PolicyHolder')),
                ('user_created', models.ForeignKey(db_column='UserCreatedUUID', on_delete=django.db.models.deletion.DO_NOTHING, related_name='contract_user_created', to=settings.AUTH_USER_MODEL)),
                ('user_updated', models.ForeignKey(db_column='UserUpdatedUUID', on_delete=django.db.models.deletion.DO_NOTHING, related_name='contract_user_updated', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'tblContract',
            },
            bases=(dirtyfields.dirtyfields.DirtyFieldsMixin, models.Model),
        ),
        migrations.CreateModel(
            name='ContractDetails',
            fields=[
                ('id', models.UUIDField(db_column='UUID', default=None, editable=False, primary_key=True, serialize=False)),
                ('is_deleted', models.BooleanField(db_column='isDeleted', default=False)),
                ('json_ext', models.JSONField(blank=True, db_column='Json_ext', null=True)),
                ('date_created', models.DateTimeField(db_column='DateCreated', null=True)),
                ('date_updated', models.DateTimeField(db_column='DateUpdated', null=True)),
                ('version', models.IntegerField(default=1)),
                ('json_param', models.JSONField(blank=True, db_column='Json_param', null=True)),
                ('contract', models.ForeignKey(db_column='ContractUUID', on_delete=django.db.models.deletion.DO_NOTHING, to='contract.Contract')),
                ('contribution_plan_bundle', models.ForeignKey(db_column='ContributionPlanBundleUUID', on_delete=django.db.models.deletion.DO_NOTHING, to='contribution_plan.ContributionPlanBundle')),
                ('policy_holder_insuree', models.ForeignKey(db_column='PolicyHolderInsureeUUID', on_delete=django.db.models.deletion.DO_NOTHING, to='policyholder.PolicyHolderInsuree')),
                ('user_created', models.ForeignKey(db_column='UserCreatedUUID', on_delete=django.db.models.deletion.DO_NOTHING, related_name='contractdetails_user_created', to=settings.AUTH_USER_MODEL)),
                ('user_updated', models.ForeignKey(db_column='UserUpdatedUUID', on_delete=django.db.models.deletion.DO_NOTHING, related_name='contractdetails_user_updated', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'tblContractDetails',
            },
            bases=(dirtyfields.dirtyfields.DirtyFieldsMixin, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalContractDetails',
            fields=[
                ('id', models.UUIDField(db_column='UUID', db_index=True, default=None, editable=False)),
                ('is_deleted', models.BooleanField(db_column='isDeleted', default=False)),
                ('json_ext', models.JSONField(blank=True, db_column='Json_ext', null=True)),
                ('date_created', models.DateTimeField(db_column='DateCreated', null=True)),
                ('date_updated', models.DateTimeField(db_column='DateUpdated', null=True)),
                ('version', models.IntegerField(default=1)),
                ('json_param', models.JSONField(blank=True, db_column='Json_param', null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('contract', models.ForeignKey(blank=True, db_column='ContractUUID', db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='contract.Contract')),
                ('contribution_plan_bundle', models.ForeignKey(blank=True, db_column='ContributionPlanBundleUUID', db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='contribution_plan.ContributionPlanBundle')),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('policy_holder_insuree', models.ForeignKey(blank=True, db_column='PolicyHolderInsureeUUID', db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='policyholder.PolicyHolderInsuree')),
                ('user_created', models.ForeignKey(blank=True, db_column='UserCreatedUUID', db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('user_updated', models.ForeignKey(blank=True, db_column='UserUpdatedUUID', db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical contract details',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalContractContributionPlanDetails',
            fields=[
                ('id', models.UUIDField(db_column='UUID', db_index=True, default=None, editable=False)),
                ('is_deleted', models.BooleanField(db_column='isDeleted', default=False)),
                ('json_ext', models.JSONField(blank=True, db_column='Json_ext', null=True)),
                ('date_created', models.DateTimeField(db_column='DateCreated', null=True)),
                ('date_updated', models.DateTimeField(db_column='DateUpdated', null=True)),
                ('version', models.IntegerField(default=1)),
                ('date_valid_from', models.DateTimeField(db_column='DateValidFrom', default=datetime.datetime.now)),
                ('date_valid_to', models.DateTimeField(blank=True, db_column='DateValidTo', null=True)),
                ('replacement_uuid', models.UUIDField(db_column='ReplacementUUID', null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('contract_details', models.ForeignKey(blank=True, db_column='ContractDetailsUUID', db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='contract.ContractDetails')),
                ('contribution_plan', models.ForeignKey(blank=True, db_column='ContributionPlanUUID', db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='contribution_plan.ContributionPlan')),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('policy', models.ForeignKey(blank=True, db_column='PolicyUUID', db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='policy.Policy')),
                ('user_created', models.ForeignKey(blank=True, db_column='UserCreatedUUID', db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('user_updated', models.ForeignKey(blank=True, db_column='UserUpdatedUUID', db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical contract contribution plan details',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalContract',
            fields=[
                ('id', models.UUIDField(db_column='UUID', db_index=True, default=None, editable=False)),
                ('is_deleted', models.BooleanField(db_column='isDeleted', default=False)),
                ('json_ext', models.JSONField(blank=True, db_column='Json_ext', null=True)),
                ('date_created', models.DateTimeField(db_column='DateCreated', null=True)),
                ('date_updated', models.DateTimeField(db_column='DateUpdated', null=True)),
                ('version', models.IntegerField(default=1)),
                ('date_valid_from', models.DateTimeField(db_column='DateValidFrom', default=datetime.datetime.now)),
                ('date_valid_to', models.DateTimeField(blank=True, db_column='DateValidTo', null=True)),
                ('replacement_uuid', models.UUIDField(db_column='ReplacementUUID', null=True)),
                ('amount_notified', models.FloatField(db_column='AmountNotified')),
                ('amount_rectified', models.FloatField(db_column='AmountRectified')),
                ('amount_due', models.FloatField(db_column='AmountDue')),
                ('date_approved', core.fields.DateTimeField(db_column='DateApproved')),
                ('date_payment_due', core.fields.DateField(db_column='DatePaymentDue')),
                ('state', models.SmallIntegerField(db_column='State')),
                ('payment_reference', models.CharField(db_column='PaymentReference', max_length=255)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('policy_holder', models.ForeignKey(blank=True, db_column='PolicyHolderUUID', db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='policyholder.PolicyHolder')),
                ('user_created', models.ForeignKey(blank=True, db_column='UserCreatedUUID', db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('user_updated', models.ForeignKey(blank=True, db_column='UserUpdatedUUID', db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical contract',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='ContractContributionPlanDetails',
            fields=[
                ('id', models.UUIDField(db_column='UUID', default=None, editable=False, primary_key=True, serialize=False)),
                ('is_deleted', models.BooleanField(db_column='isDeleted', default=False)),
                ('json_ext', models.JSONField(blank=True, db_column='Json_ext', null=True)),
                ('date_created', models.DateTimeField(db_column='DateCreated', null=True)),
                ('date_updated', models.DateTimeField(db_column='DateUpdated', null=True)),
                ('version', models.IntegerField(default=1)),
                ('date_valid_from', models.DateTimeField(db_column='DateValidFrom', default=datetime.datetime.now)),
                ('date_valid_to', models.DateTimeField(blank=True, db_column='DateValidTo', null=True)),
                ('replacement_uuid', models.UUIDField(db_column='ReplacementUUID', null=True)),
                ('contract_details', models.ForeignKey(db_column='ContractDetailsUUID', on_delete=django.db.models.deletion.DO_NOTHING, to='contract.ContractDetails')),
                ('contribution_plan', models.ForeignKey(db_column='ContributionPlanUUID', on_delete=django.db.models.deletion.DO_NOTHING, to='contribution_plan.ContributionPlan')),
                ('policy', models.ForeignKey(db_column='PolicyUUID', on_delete=django.db.models.deletion.DO_NOTHING, to='policy.Policy')),
                ('user_created', models.ForeignKey(db_column='UserCreatedUUID', on_delete=django.db.models.deletion.DO_NOTHING, related_name='contractcontributionplandetails_user_created', to=settings.AUTH_USER_MODEL)),
                ('user_updated', models.ForeignKey(db_column='UserUpdatedUUID', on_delete=django.db.models.deletion.DO_NOTHING, related_name='contractcontributionplandetails_user_updated', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'tblContractContributionPlanDetails',
            },
            bases=(dirtyfields.dirtyfields.DirtyFieldsMixin, models.Model),
        ),
    ]
