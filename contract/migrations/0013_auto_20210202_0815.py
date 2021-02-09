# Generated by Django 3.0.3 on 2021-02-02 08:15

import core.fields
import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contract', '0012_contractdetailsmutation'),
    ]

    operations = [
        migrations.AddField(
            model_name='contractcontributionplandetails',
            name='date_valid_from',
            field=core.fields.DateTimeField(db_column='DateValidFrom', default=datetime.datetime.now),
        ),
        migrations.AddField(
            model_name='contractcontributionplandetails',
            name='date_valid_to',
            field=core.fields.DateTimeField(blank=True, db_column='DateValidTo', null=True),
        ),
        migrations.AddField(
            model_name='contractcontributionplandetails',
            name='replacement_uuid',
            field=models.UUIDField(db_column='ReplacementUUID', null=True),
        ),
        migrations.AddField(
            model_name='historicalcontractcontributionplandetails',
            name='date_valid_from',
            field=core.fields.DateTimeField(db_column='DateValidFrom', default=datetime.datetime.now),
        ),
        migrations.AddField(
            model_name='historicalcontractcontributionplandetails',
            name='date_valid_to',
            field=core.fields.DateTimeField(blank=True, db_column='DateValidTo', null=True),
        ),
        migrations.AddField(
            model_name='historicalcontractcontributionplandetails',
            name='replacement_uuid',
            field=models.UUIDField(db_column='ReplacementUUID', null=True),
        ),
    ]