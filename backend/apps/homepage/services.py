"""Build the single public homepage payload from approved database rows."""

from __future__ import annotations

from typing import Any

from django.db.models import Prefetch
from django.utils import timezone

from .models import (
    ContentCard,
    ContentSection,
    FeaturedResource,
    FooterLink,
    Homepage,
    InstitutionalUpdate,
    ResourceCategory,
)
from .translation import localized

PUBLIC_LIST_LIMIT = 6


def _empty_section() -> dict[str, Any]:
    return {"title": "", "subtitle": "", "cards": []}


def _card_payload(card: ContentCard, language: str) -> dict[str, Any]:
    return {
        "id": card.id,
        "title": localized(card, "title", language),
        "description": localized(card, "description", language),
        "icon": card.icon,
        "linkLabel": localized(card, "link_label", language),
        "linkPath": card.link_path,
    }


def _section_payload(section: ContentSection, language: str) -> dict[str, Any]:
    cards = section.cards.all()
    return {
        "title": localized(section, "title", language),
        "subtitle": localized(section, "subtitle", language),
        "cards": [_card_payload(card, language) for card in cards],
    }


def build_homepage_payload(language: str) -> dict[str, Any]:
    """Return only public, approved content; never include restricted resources."""
    sections: dict[str, dict[str, Any]] = {
        ContentSection.Kind.OFFER: _empty_section(),
        ContentSection.Kind.LEARNING: _empty_section(),
        ContentSection.Kind.HERITAGE: _empty_section(),
    }
    for section in ContentSection.objects.filter(is_published=True).prefetch_related(
        Prefetch("cards", queryset=ContentCard.objects.filter(is_published=True))
    ):
        if section.kind in sections:
            sections[section.kind] = _section_payload(section, language)

    homepage = Homepage.objects.filter(is_published=True).first()
    if homepage is not None:
        popular_searches = [
            {
                "label": localized(item, "label", language),
                "query": item.query,
            }
            for item in homepage.popular_searches.filter(is_published=True)
        ]
        hero = {
            "eyebrow": localized(homepage, "hero_eyebrow", language),
            "title": localized(homepage, "hero_title", language),
            "description": localized(homepage, "hero_description", language),
            "searchLabel": localized(homepage, "search_label", language),
            "searchPlaceholder": localized(homepage, "search_placeholder", language),
            "popularSearches": popular_searches,
            "archiveFeature": {
                "title": localized(homepage, "archive_feature_title", language),
                "description": localized(homepage, "archive_feature_description", language),
                "path": homepage.archive_feature_path,
            },
        }
        membership = {
            "title": localized(homepage, "membership_title", language),
            "description": localized(homepage, "membership_description", language),
            "path": homepage.membership_path,
        }
        footer_description = localized(homepage, "footer_description", language)
    else:
        hero = {
            "eyebrow": "",
            "title": "",
            "description": "",
            "searchLabel": "",
            "searchPlaceholder": "",
            "popularSearches": [],
            "archiveFeature": {"title": "", "description": "", "path": ""},
        }
        membership = {"title": "", "description": "", "path": "/membership"}
        footer_description = ""

    categories = [
        {
            "label": localized(item, "label", language),
            "slug": item.slug,
            "description": localized(item, "description", language),
            "icon": item.icon,
            "query": item.search_query,
        }
        for item in ResourceCategory.objects.filter(is_active=True)
    ]

    featured = [
        {
            "id": item.id,
            "title": localized(item, "title", language),
            "resourceType": item.resource_type,
            "source": item.source,
            "sourceId": item.source_id,
            "description": localized(item, "description", language),
            "detailPath": item.detail_path,
            "thumbnailPath": item.thumbnail_path,
            "accessStatus": item.access,
        }
        for item in FeaturedResource.objects.filter(
            is_published=True, access=FeaturedResource.Access.PUBLIC
        )[:PUBLIC_LIST_LIMIT]
    ]

    updates = [
        {
            "id": item.id,
            "kind": item.kind,
            "title": localized(item, "title", language),
            "summary": localized(item, "summary", language),
            "detailPath": item.detail_path,
            "imagePath": item.image_path,
            "publishedAt": item.published_at.isoformat(),
            "eventDate": item.event_date.isoformat() if item.event_date else None,
        }
        for item in InstitutionalUpdate.objects.filter(
            is_published=True, published_at__lte=timezone.now()
        )[:PUBLIC_LIST_LIMIT]
    ]

    footer_groups: dict[str, list[dict[str, Any]]] = {
        group: [] for group, _ in FooterLink.Group.choices
    }
    for link in FooterLink.objects.filter(is_approved=True):
        footer_groups[link.group].append(
            {
                "label": localized(link, "label", language),
                "url": link.url,
                "icon": link.icon,
            }
        )

    return {
        "language": language,
        "hero": hero,
        "offers": sections[ContentSection.Kind.OFFER],
        "heritage": sections[ContentSection.Kind.HERITAGE],
        "learning": sections[ContentSection.Kind.LEARNING],
        "categories": categories,
        "featuredResources": featured,
        "updates": updates,
        "membership": membership,
        "footer": {"description": footer_description, "groups": footer_groups},
    }
