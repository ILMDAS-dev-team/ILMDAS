"""Move the legacy User.role value into UserRole, then drop the field (ILMDAS-28 follow-up).

Every existing account also receives the member role, matching what new accounts get.
"""

from django.db import migrations

LEGACY_TO_ROLE_CODE = {
    "member": "member",
    "staff": "librarian",
    "archivist": "digital_archivist",
    "administrator": "system_administrator",
}


def copy_legacy_roles(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    Role = apps.get_model("accounts", "Role")
    UserRole = apps.get_model("accounts", "UserRole")
    roles = {role.code: role for role in Role.objects.all()}
    member = roles.get("member")
    for user in User.objects.all().only("id", "role"):
        codes = {LEGACY_TO_ROLE_CODE.get(user.role)} | ({"member"} if member else set())
        for code in codes:
            role = roles.get(code)
            if role is not None:
                UserRole.objects.get_or_create(user=user, role=role)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_seed_roles"),
    ]

    operations = [
        migrations.RunPython(copy_legacy_roles, migrations.RunPython.noop),
        migrations.RemoveField(model_name="user", name="role"),
    ]
