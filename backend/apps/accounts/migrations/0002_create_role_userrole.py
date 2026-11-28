"""Create the Role and UserRole tables (ILMDAS-28).

These were first added by editing 0001_initial, which databases migrated from main
had already applied, so they never got the tables. This migration records both
models in the migration state and creates each table only if it is missing, so it
works for databases from main (tables absent) and from develop (tables present).
"""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

MODELS = ("Role", "UserRole")


def create_missing_tables(apps, schema_editor):
    existing = set(schema_editor.connection.introspection.table_names())
    for name in MODELS:
        model = apps.get_model("accounts", name)
        if model._meta.db_table not in existing:
            schema_editor.create_model(model)


def drop_tables(apps, schema_editor):
    existing = set(schema_editor.connection.introspection.table_names())
    for name in reversed(MODELS):
        model = apps.get_model("accounts", name)
        if model._meta.db_table in existing:
            schema_editor.delete_model(model)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name="Role",
                    fields=[
                        (
                            "id",
                            models.BigAutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name="ID",
                            ),
                        ),
                        ("name", models.CharField(max_length=100, unique=True)),
                        ("code", models.CharField(max_length=50, unique=True)),
                        ("description", models.TextField(blank=True)),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                    ],
                    options={
                        "ordering": ["name"],
                    },
                ),
                migrations.CreateModel(
                    name="UserRole",
                    fields=[
                        (
                            "id",
                            models.BigAutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name="ID",
                            ),
                        ),
                        ("assigned_at", models.DateTimeField(auto_now_add=True)),
                        (
                            "assigned_by",
                            models.ForeignKey(
                                blank=True,
                                null=True,
                                on_delete=django.db.models.deletion.SET_NULL,
                                related_name="assigned_user_roles",
                                to=settings.AUTH_USER_MODEL,
                            ),
                        ),
                        (
                            "role",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="user_roles",
                                to="accounts.role",
                            ),
                        ),
                        (
                            "user",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="user_roles",
                                to=settings.AUTH_USER_MODEL,
                            ),
                        ),
                    ],
                    options={
                        "ordering": ["-assigned_at"],
                        "unique_together": {("user", "role")},
                    },
                ),
            ],
            database_operations=[],
        ),
        # Runs after the models are in the migration state, so get_model() finds them.
        migrations.RunPython(create_missing_tables, drop_tables),
    ]
