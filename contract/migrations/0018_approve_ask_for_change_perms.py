import logging

from django.db import migrations

from core.utils import insert_role_right_for_system

logger = logging.getLogger(__name__)


def add_contract(apps, schema_editor):
    insert_role_right_for_system(256, 152108, apps)


class Migration(migrations.Migration):
    dependencies = [
        ('contract', '0017_contract_roles_for_admin')
    ]

    operations = [
        migrations.RunPython(add_contract, None)
    ]
