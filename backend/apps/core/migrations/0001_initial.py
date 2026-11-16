"""Initial object-reference table. File bytes are not stored here."""

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ObjectReference",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("object_key", models.CharField(max_length=512, unique=True)),
                ("reference", models.CharField(max_length=1024)),
                ("checksum_sha256", models.CharField(max_length=64)),
                ("content_type", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
