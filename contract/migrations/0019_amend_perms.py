import logging

from django.db import migrations

from core.utils import insert_role_right_for_system

logger = logging.getLogger(__name__)


def add_rights(apps, schema_editor):
    insert_role_right_for_system(256, 152109, apps)  # contract approve


class Migration(migrations.Migration):
    dependencies = [
        ('contract', '0018_approve_ask_for_change_perms')
    ]

    operations = [
        migrations.RunPython(add_rights),
    ]
