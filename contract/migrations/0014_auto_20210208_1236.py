# Generated by Django 3.0.3 on 2021-02-08 12:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contribution', '0001_initial'),
        ('contract', '0013_auto_20210202_0815'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contractcontributionplandetails',
            name='contribution',
            field=models.ForeignKey(blank=True, db_column='ContributionId', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='contract_contribution_plan_details', to='contribution.Premium'),
        ),
    ]
