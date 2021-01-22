# Generated by Django 3.0.3 on 2021-01-18 14:27

import core.fields
import datetime
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contract', '0008_auto_20201230_1052'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contract',
            name='date_created',
            field=core.fields.DateTimeField(db_column='DateCreated', null=True),
        ),
        migrations.AlterField(
            model_name='contract',
            name='date_updated',
            field=core.fields.DateTimeField(db_column='DateUpdated', null=True),
        ),
        migrations.AlterField(
            model_name='contract',
            name='date_valid_from',
            field=core.fields.DateTimeField(db_column='DateValidFrom', default=datetime.datetime.now),
        ),
        migrations.AlterField(
            model_name='contract',
            name='date_valid_to',
            field=core.fields.DateTimeField(blank=True, db_column='DateValidTo', null=True),
        ),
        migrations.AlterField(
            model_name='contractcontributionplandetails',
            name='date_created',
            field=core.fields.DateTimeField(db_column='DateCreated', null=True),
        ),
        migrations.AlterField(
            model_name='contractcontributionplandetails',
            name='date_updated',
            field=core.fields.DateTimeField(db_column='DateUpdated', null=True),
        ),
        migrations.AlterField(
            model_name='contractdetails',
            name='date_created',
            field=core.fields.DateTimeField(db_column='DateCreated', null=True),
        ),
        migrations.AlterField(
            model_name='contractdetails',
            name='date_updated',
            field=core.fields.DateTimeField(db_column='DateUpdated', null=True),
        ),
        migrations.AlterField(
            model_name='historicalcontract',
            name='date_created',
            field=core.fields.DateTimeField(db_column='DateCreated', null=True),
        ),
        migrations.AlterField(
            model_name='historicalcontract',
            name='date_updated',
            field=core.fields.DateTimeField(db_column='DateUpdated', null=True),
        ),
        migrations.AlterField(
            model_name='historicalcontract',
            name='date_valid_from',
            field=core.fields.DateTimeField(db_column='DateValidFrom', default=datetime.datetime.now),
        ),
        migrations.AlterField(
            model_name='historicalcontract',
            name='date_valid_to',
            field=core.fields.DateTimeField(blank=True, db_column='DateValidTo', null=True),
        ),
        migrations.AlterField(
            model_name='historicalcontractcontributionplandetails',
            name='date_created',
            field=core.fields.DateTimeField(db_column='DateCreated', null=True),
        ),
        migrations.AlterField(
            model_name='historicalcontractcontributionplandetails',
            name='date_updated',
            field=core.fields.DateTimeField(db_column='DateUpdated', null=True),
        ),
        migrations.AlterField(
            model_name='historicalcontractdetails',
            name='date_created',
            field=core.fields.DateTimeField(db_column='DateCreated', null=True),
        ),
        migrations.AlterField(
            model_name='historicalcontractdetails',
            name='date_updated',
            field=core.fields.DateTimeField(db_column='DateUpdated', null=True),
        ),
    ]