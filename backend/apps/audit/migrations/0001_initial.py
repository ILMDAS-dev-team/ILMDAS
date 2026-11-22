"""Initial migration for AuditRecord model."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AuditRecord",
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
                ("timestamp", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("actor_username", models.CharField(blank=True, max_length=150)),
                ("action", models.CharField(db_index=True, max_length=128)),
                ("object_type", models.CharField(blank=True, max_length=128)),
                ("object_id", models.CharField(blank=True, max_length=255)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("correlation_id", models.CharField(blank=True, max_length=64)),
                ("details", models.JSONField(blank=True, default=dict)),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="audit_records",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-timestamp"],
            },
        ),
        migrations.AddIndex(
            model_name="auditrecord",
            index=models.Index(fields=["action", "timestamp"], name="audit_rec_action_ts_idx"),
        ),
        migrations.AddIndex(
            model_name="auditrecord",
            index=models.Index(fields=["object_type", "object_id"], name="audit_rec_obj_idx"),
        ),
    ]
