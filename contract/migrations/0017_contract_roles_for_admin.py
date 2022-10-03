import logging

from django.db import migrations

logger = logging.getLogger(__name__)


MIGRATION_SQL = """
    /* Contract */
    DECLARE @SystemRole INT
    SELECT @SystemRole = role.RoleID from tblRole role where IsSystem=64;
    /* Contract search*/
    IF NOT EXISTS (SELECT * FROM [tblRoleRight] WHERE [RoleID] = @SystemRole AND [RightID] = 152101)
    BEGIN
        INSERT [dbo].[tblRoleRight] ([RoleID], [RightID], [ValidityFrom]) 
        VALUES (@SystemRole, 152101, CURRENT_TIMESTAMP)
    END 
    /* Contract create*/
    IF NOT EXISTS (SELECT * FROM [tblRoleRight] WHERE [RoleID] = @SystemRole AND [RightID] = 152102)
    BEGIN
        INSERT [dbo].[tblRoleRight] ([RoleID], [RightID], [ValidityFrom]) 
        VALUES (@SystemRole, 152102, CURRENT_TIMESTAMP)
    END 
    /* Contract update*/
    IF NOT EXISTS (SELECT * FROM [tblRoleRight] WHERE [RoleID] = @SystemRole AND [RightID] = 152103)
    BEGIN
        INSERT [dbo].[tblRoleRight] ([RoleID], [RightID], [ValidityFrom]) 
        VALUES (@SystemRole, 152103, CURRENT_TIMESTAMP)
    END 
    /* Contract delete*/
    IF NOT EXISTS (SELECT * FROM [tblRoleRight] WHERE [RoleID] = @SystemRole AND [RightID] = 152104)
    BEGIN
        INSERT [dbo].[tblRoleRight] ([RoleID], [RightID], [ValidityFrom]) 
        VALUES (@SystemRole, 152104, CURRENT_TIMESTAMP)
    END 
    /* Contract renew*/
    IF NOT EXISTS (SELECT * FROM [tblRoleRight] WHERE [RoleID] = @SystemRole AND [RightID] = 152106)
    BEGIN
        INSERT [dbo].[tblRoleRight] ([RoleID], [RightID], [ValidityFrom]) 
        VALUES (@SystemRole, 152106, CURRENT_TIMESTAMP)
    END 
    /* Contract submit */
    IF NOT EXISTS (SELECT * FROM [tblRoleRight] WHERE [RoleID] = @SystemRole AND [RightID] = 152107)
    BEGIN
        INSERT [dbo].[tblRoleRight] ([RoleID], [RightID], [ValidityFrom]) 
        VALUES (@SystemRole, 152107, CURRENT_TIMESTAMP)
    END 
    /* payment approve */
    IF NOT EXISTS (SELECT * FROM [tblRoleRight] WHERE [RoleID] = @SystemRole AND [RightID] = 101408)
    BEGIN
        INSERT [dbo].[tblRoleRight] ([RoleID], [RightID], [ValidityFrom]) 
        VALUES (@SystemRole, 101408, CURRENT_TIMESTAMP)
    END 
"""


class Migration(migrations.Migration):
    dependencies = [
        ('contract', '0016_auto_20210208_1508')
    ]

    operations = [
        migrations.RunSQL(sql=MIGRATION_SQL),
    ]
