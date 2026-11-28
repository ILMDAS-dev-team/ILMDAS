"""Serializers for authorized management of public website content."""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from .constants import SUPPORTED_LANGUAGES
from .models import (
    ContentCard,
    ContentSection,
    FeaturedResource,
    FooterLink,
    Homepage,
    InstitutionalUpdate,
    PopularSearch,
    ResourceCategory,
)


class TranslationValidatorMixin:
    """Translation overrides must be keyed by an ILMDAS language code."""

    def validate_translations(self, value: Any) -> dict[str, dict[str, str]]:
        if not isinstance(value, dict):
            raise serializers.ValidationError("Translations must be an object.")
        for code, overrides in value.items():
            if code not in SUPPORTED_LANGUAGES:
                raise serializers.ValidationError(f"Unsupported language code: {code}.")
            if not isinstance(overrides, dict) or any(
                not isinstance(item, str) for item in overrides.values()
            ):
                raise serializers.ValidationError("Translations must map fields to strings.")
        return value


class HomepageSerializer(TranslationValidatorMixin, serializers.ModelSerializer):
    class Meta:
        model = Homepage
        fields = [
            "id",
            "hero_title",
            "hero_description",
            "hero_eyebrow",
            "search_label",
            "search_placeholder",
            "archive_feature_title",
            "archive_feature_description",
            "archive_feature_path",
            "membership_title",
            "membership_description",
            "membership_path",
            "footer_description",
            "translations",
            "is_published",
            "updated_at",
            "updated_by",
        ]
        read_only_fields = ["id", "updated_at", "updated_by"]

    def validate_is_published(self, value: bool) -> bool:
        """Keep the public homepage unambiguous; the database enforces this too."""
        if value:
            published = Homepage.objects.filter(is_published=True)
            if self.instance is not None and self.instance.pk is not None:
                published = published.exclude(pk=self.instance.pk)
            if published.exists():
                raise serializers.ValidationError(
                    "Unpublish the current homepage before publishing another one."
                )
        return value


class PopularSearchSerializer(TranslationValidatorMixin, serializers.ModelSerializer):
    class Meta:
        model = PopularSearch
        fields = ["id", "homepage", "label", "query", "sort_order", "is_published", "translations"]
        read_only_fields = ["id"]


class ResourceCategorySerializer(TranslationValidatorMixin, serializers.ModelSerializer):
    class Meta:
        model = ResourceCategory
        fields = [
            "id",
            "label",
            "slug",
            "description",
            "icon",
            "search_query",
            "sort_order",
            "is_active",
            "translations",
        ]
        read_only_fields = ["id"]


class ContentSectionSerializer(TranslationValidatorMixin, serializers.ModelSerializer):
    class Meta:
        model = ContentSection
        fields = [
            "id",
            "slug",
            "kind",
            "title",
            "subtitle",
            "sort_order",
            "is_published",
            "translations",
        ]
        read_only_fields = ["id"]


class ContentCardSerializer(TranslationValidatorMixin, serializers.ModelSerializer):
    class Meta:
        model = ContentCard
        fields = [
            "id",
            "section",
            "title",
            "description",
            "icon",
            "link_label",
            "link_path",
            "sort_order",
            "is_published",
            "translations",
        ]
        read_only_fields = ["id"]


class FeaturedResourceSerializer(TranslationValidatorMixin, serializers.ModelSerializer):
    class Meta:
        model = FeaturedResource
        fields = [
            "id",
            "title",
            "resource_type",
            "source",
            "source_id",
            "description",
            "detail_path",
            "thumbnail_path",
            "access",
            "sort_order",
            "is_published",
            "translations",
        ]
        read_only_fields = ["id"]


class InstitutionalUpdateSerializer(TranslationValidatorMixin, serializers.ModelSerializer):
    class Meta:
        model = InstitutionalUpdate
        fields = [
            "id",
            "kind",
            "title",
            "summary",
            "detail_path",
            "image_path",
            "published_at",
            "event_date",
            "is_published",
            "translations",
        ]
        read_only_fields = ["id"]


class FooterLinkSerializer(TranslationValidatorMixin, serializers.ModelSerializer):
    class Meta:
        model = FooterLink
        fields = [
            "id",
            "group",
            "label",
            "url",
            "icon",
            "sort_order",
            "is_approved",
            "translations",
        ]
        read_only_fields = ["id"]
