import logging

from django.db import migrations

logger = logging.getLogger(__name__)


MIGRATION_SQL = """
    /* Contract */
    DECLARE @SystemRole INT
    SELECT @SystemRole = role.RoleID from tblRole role where IsSystem=256;
    /* Contract aprrove or counter */
    IF NOT EXISTS (SELECT * FROM [tblRoleRight] WHERE [RoleID] = @SystemRole AND [RightID] = 152108)
    BEGIN
        INSERT [dbo].[tblRoleRight] ([RoleID], [RightID], [ValidityFrom]) 
        VALUES (@SystemRole, 152108, CURRENT_TIMESTAMP)
    END 
"""


class Migration(migrations.Migration):
    dependencies = [
        ('contract', '0017_contract_roles_for_admin')
    ]

    operations = [
        migrations.RunSQL(MIGRATION_SQL)
    ]
