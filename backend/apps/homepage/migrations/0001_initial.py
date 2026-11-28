"""Initial tables for approved public homepage content."""

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models

import apps.homepage.validators


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ContentSection",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("translations", models.JSONField(blank=True, default=dict)),
                ("slug", models.SlugField(max_length=120, unique=True)),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("offer", "What We Offer"),
                            ("learning", "Learning & Research"),
                            ("heritage", "Heritage & Digital Archive"),
                        ],
                        default="offer",
                        max_length=32,
                        unique=True,
                    ),
                ),
                ("title", models.CharField(max_length=255)),
                ("subtitle", models.TextField(blank=True)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("is_published", models.BooleanField(default=False)),
            ],
            options={
                "ordering": ["sort_order", "id"],
            },
        ),
        migrations.CreateModel(
            name="FooterLink",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("translations", models.JSONField(blank=True, default=dict)),
                (
                    "group",
                    models.CharField(
                        choices=[
                            ("quick_links", "Quick links"),
                            ("resources", "Resources"),
                            ("connect", "Connect"),
                        ],
                        default="quick_links",
                        max_length=32,
                    ),
                ),
                ("label", models.CharField(max_length=120)),
                (
                    "url",
                    models.CharField(
                        max_length=512, validators=[apps.homepage.validators.validate_link_url]
                    ),
                ),
                ("icon", models.CharField(blank=True, max_length=60)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("is_approved", models.BooleanField(default=False)),
            ],
            options={
                "ordering": ["group", "sort_order", "id"],
            },
        ),
        migrations.CreateModel(
            name="InstitutionalUpdate",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("translations", models.JSONField(blank=True, default=dict)),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("announcement", "Announcement"),
                            ("news", "Institutional news"),
                            ("cultural_program", "Cultural program"),
                            ("research_activity", "Research activity"),
                            ("event", "Event"),
                        ],
                        default="announcement",
                        max_length=32,
                    ),
                ),
                ("title", models.CharField(max_length=255)),
                ("summary", models.TextField(blank=True)),
                (
                    "detail_path",
                    models.CharField(
                        blank=True,
                        max_length=512,
                        validators=[apps.homepage.validators.validate_local_path],
                    ),
                ),
                (
                    "image_path",
                    models.CharField(
                        blank=True,
                        max_length=512,
                        validators=[apps.homepage.validators.validate_local_path],
                    ),
                ),
                (
                    "published_at",
                    models.DateTimeField(db_index=True, default=django.utils.timezone.now),
                ),
                ("event_date", models.DateField(blank=True, null=True)),
                ("is_published", models.BooleanField(default=False)),
            ],
            options={
                "ordering": ["-published_at", "-id"],
            },
        ),
        migrations.CreateModel(
            name="ResourceCategory",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("translations", models.JSONField(blank=True, default=dict)),
                ("label", models.CharField(max_length=120)),
                ("slug", models.SlugField(max_length=120, unique=True)),
                ("description", models.CharField(blank=True, max_length=255)),
                ("icon", models.CharField(blank=True, max_length=60)),
                ("search_query", models.CharField(blank=True, max_length=255)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(default=False)),
            ],
            options={
                "ordering": ["sort_order", "id"],
            },
        ),
        migrations.CreateModel(
            name="ContentCard",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("translations", models.JSONField(blank=True, default=dict)),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("icon", models.CharField(blank=True, max_length=60)),
                ("link_label", models.CharField(blank=True, max_length=120)),
                (
                    "link_path",
                    models.CharField(
                        blank=True,
                        max_length=512,
                        validators=[apps.homepage.validators.validate_local_path],
                    ),
                ),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("is_published", models.BooleanField(default=True)),
                (
                    "section",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="cards",
                        to="homepage.contentsection",
                    ),
                ),
            ],
            options={
                "ordering": ["sort_order", "id"],
            },
        ),
        migrations.CreateModel(
            name="FeaturedResource",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("translations", models.JSONField(blank=True, default=dict)),
                ("title", models.CharField(max_length=255)),
                (
                    "resource_type",
                    models.CharField(
                        choices=[
                            ("ebook", "E-book"),
                            ("video", "Video"),
                            ("audio", "Audio"),
                            ("journal", "Journal"),
                            ("historical_document", "Historical document"),
                            ("oral_history", "Oral history"),
                            ("research", "Research publication"),
                            ("manuscript", "Manuscript"),
                        ],
                        max_length=32,
                    ),
                ),
                (
                    "source",
                    models.CharField(
                        choices=[("catalogue", "Catalogue"), ("archive", "Digital archive")],
                        max_length=32,
                    ),
                ),
                ("source_id", models.CharField(max_length=128)),
                ("description", models.TextField(blank=True)),
                (
                    "detail_path",
                    models.CharField(
                        max_length=512, validators=[apps.homepage.validators.validate_local_path]
                    ),
                ),
                (
                    "thumbnail_path",
                    models.CharField(
                        blank=True,
                        max_length=512,
                        validators=[apps.homepage.validators.validate_local_path],
                    ),
                ),
                (
                    "access",
                    models.CharField(
                        choices=[("public", "Open access"), ("restricted", "Sign-in required")],
                        default="public",
                        max_length=16,
                    ),
                ),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("is_published", models.BooleanField(default=False)),
            ],
            options={
                "ordering": ["sort_order", "id"],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("source", "source_id"), name="homepage_featured_unique_source"
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="Homepage",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("translations", models.JSONField(blank=True, default=dict)),
                ("hero_title", models.CharField(max_length=255)),
                ("hero_description", models.TextField(blank=True)),
                ("hero_eyebrow", models.CharField(blank=True, max_length=120)),
                ("search_label", models.CharField(blank=True, max_length=120)),
                ("search_placeholder", models.CharField(blank=True, max_length=200)),
                ("archive_feature_title", models.CharField(blank=True, max_length=255)),
                ("archive_feature_description", models.TextField(blank=True)),
                (
                    "archive_feature_path",
                    models.CharField(
                        blank=True,
                        max_length=512,
                        validators=[apps.homepage.validators.validate_local_path],
                    ),
                ),
                ("membership_title", models.CharField(blank=True, max_length=255)),
                ("membership_description", models.TextField(blank=True)),
                (
                    "membership_path",
                    models.CharField(
                        default="/membership",
                        max_length=512,
                        validators=[apps.homepage.validators.validate_local_path],
                    ),
                ),
                ("footer_description", models.TextField(blank=True)),
                ("is_published", models.BooleanField(default=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="homepage_updates",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Homepage",
                "verbose_name_plural": "Homepage",
                "ordering": ["-updated_at"],
            },
        ),
        migrations.CreateModel(
            name="PopularSearch",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("translations", models.JSONField(blank=True, default=dict)),
                ("label", models.CharField(max_length=120)),
                ("query", models.CharField(max_length=255)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("is_published", models.BooleanField(default=True)),
                (
                    "homepage",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="popular_searches",
                        to="homepage.homepage",
                    ),
                ),
            ],
            options={
                "ordering": ["sort_order", "id"],
            },
        ),
    ]
