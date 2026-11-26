"""Seed the seven named ILMDAS roles. Idempotent: uses get_or_create."""

from django.db import migrations

ROLE_DATA = [
    (
        "system_administrator",
        "System Administrator",
        "Full system administration including role management.",
    ),
    ("librarian", "Librarian", "Catalogue and circulation operations."),
    ("digital_archivist", "Digital Archivist", "Digital object and archive management."),
    ("journal_editor", "Journal Editor", "Journal publishing operations."),
    ("member", "Member", "Standard member access to public and member features."),
    ("manager", "Manager", "Management oversight across modules."),
    (
        "integration_administrator",
        "Integration Administrator",
        "Integration and external system configuration.",
    ),
]


def seed_roles(apps, schema_editor):
    Role = apps.get_model("accounts", "Role")
    for code, name, description in ROLE_DATA:
        Role.objects.get_or_create(code=code, defaults={"name": name, "description": description})


def unseed_roles(apps, schema_editor):
    Role = apps.get_model("accounts", "Role")
    Role.objects.filter(code__in=[code for code, _, _ in ROLE_DATA]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_create_role_userrole"),
    ]

    operations = [
        migrations.RunPython(seed_roles, unseed_roles),
    ]
