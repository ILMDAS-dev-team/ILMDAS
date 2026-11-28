"""Tables for approved public website content managed by authorized ILMDAS users.

Every row published to the public API must be explicitly approved (``is_published``
or ``is_approved``). Restricted archive resources are never included in public
payloads. Translations are stored as ``{"om": {"title": "..."}, "am": {...}}`` and
fall back to the base field when a translation is missing.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone

from .validators import validate_link_url, validate_local_path


class TranslatedContent(models.Model):
    """Base class for content with approved translation overrides."""

    translations = models.JSONField(default=dict, blank=True)

    class Meta:
        abstract = True


class Homepage(TranslatedContent):
    """The single published homepage configuration. Content teams edit its rows."""

    hero_title = models.CharField(max_length=255)
    hero_description = models.TextField(blank=True)
    hero_eyebrow = models.CharField(max_length=120, blank=True)
    search_label = models.CharField(max_length=120, blank=True)
    search_placeholder = models.CharField(max_length=200, blank=True)
    archive_feature_title = models.CharField(max_length=255, blank=True)
    archive_feature_description = models.TextField(blank=True)
    archive_feature_path = models.CharField(
        max_length=512, blank=True, validators=[validate_local_path]
    )
    membership_title = models.CharField(max_length=255, blank=True)
    membership_description = models.TextField(blank=True)
    membership_path = models.CharField(
        max_length=512, default="/membership", validators=[validate_local_path]
    )
    footer_description = models.TextField(blank=True)
    is_published = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="homepage_updates",
    )

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "Homepage"
        verbose_name_plural = "Homepage"

    def __str__(self) -> str:
        return self.hero_title


class PopularSearch(TranslatedContent):
    """An approved search suggestion shown under the hero search field."""

    homepage = models.ForeignKey(
        Homepage, on_delete=models.CASCADE, related_name="popular_searches"
    )
    label = models.CharField(max_length=120)
    query = models.CharField(max_length=255)
    sort_order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self) -> str:
        return self.label


class ResourceCategory(TranslatedContent):
    """A resource category. Inactive categories are hidden from the public site."""

    label = models.CharField(max_length=120)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.CharField(max_length=255, blank=True)
    icon = models.CharField(max_length=60, blank=True)
    search_query = models.CharField(max_length=255, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=False)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self) -> str:
        return self.label


class ContentSection(TranslatedContent):
    """A named homepage section such as What We Offer or Learning & Research."""

    class Kind(models.TextChoices):
        OFFER = "offer", "What We Offer"
        LEARNING = "learning", "Learning & Research"
        HERITAGE = "heritage", "Heritage & Digital Archive"

    slug = models.SlugField(max_length=120, unique=True)
    kind = models.CharField(max_length=32, choices=Kind.choices, default=Kind.OFFER, unique=True)
    title = models.CharField(max_length=255)
    subtitle = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=False)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self) -> str:
        return self.title


class ContentCard(TranslatedContent):
    """A reusable card inside a content section."""

    section = models.ForeignKey(ContentSection, on_delete=models.CASCADE, related_name="cards")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=60, blank=True)
    link_label = models.CharField(max_length=120, blank=True)
    link_path = models.CharField(max_length=512, blank=True, validators=[validate_local_path])
    sort_order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self) -> str:
        return self.title


class FeaturedResource(TranslatedContent):
    """Curated reference to a real catalogue or archive resource.

    ``source``/``source_id`` identify the record in the owning app. Details are
    never invented here: until the owning app exposes the resource it is not
    published. Restricted resources are excluded from public responses.
    """

    class ResourceType(models.TextChoices):
        EBOOK = "ebook", "E-book"
        VIDEO = "video", "Video"
        AUDIO = "audio", "Audio"
        JOURNAL = "journal", "Journal"
        HISTORICAL_DOCUMENT = "historical_document", "Historical document"
        ORAL_HISTORY = "oral_history", "Oral history"
        RESEARCH = "research", "Research publication"
        MANUSCRIPT = "manuscript", "Manuscript"

    class Source(models.TextChoices):
        CATALOGUE = "catalogue", "Catalogue"
        ARCHIVE = "archive", "Digital archive"

    class Access(models.TextChoices):
        PUBLIC = "public", "Open access"
        RESTRICTED = "restricted", "Sign-in required"

    title = models.CharField(max_length=255)
    resource_type = models.CharField(max_length=32, choices=ResourceType.choices)
    source = models.CharField(max_length=32, choices=Source.choices)
    source_id = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    detail_path = models.CharField(max_length=512, validators=[validate_local_path])
    thumbnail_path = models.CharField(max_length=512, blank=True, validators=[validate_local_path])
    access = models.CharField(max_length=16, choices=Access.choices, default=Access.PUBLIC)
    sort_order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=False)

    class Meta:
        ordering = ["sort_order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["source", "source_id"], name="homepage_featured_unique_source"
            )
        ]

    def __str__(self) -> str:
        return self.title


class InstitutionalUpdate(TranslatedContent):
    """An approved announcement, news item, program, activity or event."""

    class Kind(models.TextChoices):
        ANNOUNCEMENT = "announcement", "Announcement"
        NEWS = "news", "Institutional news"
        CULTURAL_PROGRAM = "cultural_program", "Cultural program"
        RESEARCH_ACTIVITY = "research_activity", "Research activity"
        EVENT = "event", "Event"

    kind = models.CharField(max_length=32, choices=Kind.choices, default=Kind.ANNOUNCEMENT)
    title = models.CharField(max_length=255)
    summary = models.TextField(blank=True)
    detail_path = models.CharField(max_length=512, blank=True, validators=[validate_local_path])
    image_path = models.CharField(max_length=512, blank=True, validators=[validate_local_path])
    published_at = models.DateTimeField(default=timezone.now, db_index=True)
    event_date = models.DateField(null=True, blank=True)
    is_published = models.BooleanField(default=False)

    class Meta:
        ordering = ["-published_at", "-id"]

    def __str__(self) -> str:
        return self.title


class FooterLink(TranslatedContent):
    """An approved footer link, grouped by purpose."""

    class Group(models.TextChoices):
        QUICK_LINKS = "quick_links", "Quick links"
        RESOURCES = "resources", "Resources"
        CONNECT = "connect", "Connect"

    group = models.CharField(max_length=32, choices=Group.choices, default=Group.QUICK_LINKS)
    label = models.CharField(max_length=120)
    url = models.CharField(max_length=512, validators=[validate_link_url])
    icon = models.CharField(max_length=60, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_approved = models.BooleanField(default=False)

    class Meta:
        ordering = ["group", "sort_order", "id"]

    def __str__(self) -> str:
        return self.label
