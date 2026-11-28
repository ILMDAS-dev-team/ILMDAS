"""Seed the guest role that every new account starts with (ILMDAS-550).

Existing accounts keep their roles: current members are not moved to guest.
"""

from django.db import migrations


def seed_guest(apps, schema_editor):
    Role = apps.get_model("accounts", "Role")
    Role.objects.get_or_create(
        code="guest",
        defaults={
            "name": "Guest",
            "description": (
                "Registered account without a membership: public discovery and own account."
            ),
        },
    )


def unseed_guest(apps, schema_editor):
    Role = apps.get_model("accounts", "Role")
    Role.objects.filter(code="guest").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0004_user_status_check_constraint"),
    ]

    operations = [
        migrations.RunPython(seed_guest, unseed_guest),
    ]
