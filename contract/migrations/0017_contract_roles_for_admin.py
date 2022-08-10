import logging

from django.db import migrations

from core.utils import insert_role_right_for_system

logger = logging.getLogger(__name__)


def add_rights(apps, schema_editor):
    insert_role_right_for_system(64, 152101)  # contract search
    insert_role_right_for_system(64, 152102)  # contract create
    insert_role_right_for_system(64, 152103)  # contract update
    insert_role_right_for_system(64, 152104)  # contract delete
    insert_role_right_for_system(64, 152106)  # contract renew
    insert_role_right_for_system(64, 152107)  # contract submit
    insert_role_right_for_system(64, 152108)  # contract approve


class Migration(migrations.Migration):
    dependencies = [
        ('contract', '0016_auto_20210208_1508')
    ]

    operations = [
        migrations.RunPython(add_rights)
    ]
