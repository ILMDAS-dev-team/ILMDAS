"""Anonymous homepage API: only approved public content is returned."""

from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace

import pytest
from django.utils import timezone

from apps.accounts.testing import make_user
from apps.homepage.models import (
    ContentCard,
    ContentSection,
    FeaturedResource,
    FooterLink,
    Homepage,
    InstitutionalUpdate,
    PopularSearch,
    ResourceCategory,
)

HOME_URL = "/api/v1/website/home/"


@pytest.fixture
def public_content(db):
    homepage = Homepage.objects.create(
        hero_title="A world of knowledge.",
        hero_description="Explore the library and archive.",
        hero_eyebrow="DISCOVER",
        search_label="SEARCH THE LIBRARY & ARCHIVE",
        search_placeholder="Title, author, subject or keyword",
        archive_feature_title="Digital Archive",
        archive_feature_description="Historical documents and oral histories.",
        archive_feature_path="/archive",
        membership_title="Become a Member",
        membership_description="Join the ILMDAS community.",
        membership_path="/membership",
        footer_description="Library and digital archive.",
        is_published=True,
        translations={"om": {"hero_title": "Addunyaa beekumsaa."}},
    )
    PopularSearch.objects.create(homepage=homepage, label="Afaan Oromo", query="Afaan Oromo")
    PopularSearch.objects.create(
        homepage=homepage, label="Hidden", query="hidden", is_published=False
    )

    offer = ContentSection.objects.create(
        slug="offer", kind=ContentSection.Kind.OFFER, title="What We Offer", is_published=True
    )
    ContentCard.objects.create(section=offer, title="Extensive Collection", sort_order=1)
    ContentCard.objects.create(section=offer, title="Hidden Card", is_published=False, sort_order=2)
    learning = ContentSection.objects.create(
        slug="learning",
        kind=ContentSection.Kind.LEARNING,
        title="Learning & Research",
        is_published=True,
    )
    ContentCard.objects.create(section=learning, title="Discover")
    ContentSection.objects.create(
        slug="heritage", kind=ContentSection.Kind.HERITAGE, title="Heritage", is_published=False
    )

    ResourceCategory.objects.create(label="E-books", slug="ebooks", is_active=True)
    ResourceCategory.objects.create(label="Video", slug="video", is_active=False)

    public_resource = FeaturedResource.objects.create(
        title="Oral History Collection",
        resource_type=FeaturedResource.ResourceType.ORAL_HISTORY,
        source=FeaturedResource.Source.ARCHIVE,
        source_id="archive-1",
        detail_path="/archive/archive-1/",
        is_published=True,
    )
    restricted = FeaturedResource.objects.create(
        title="Restricted Manuscript",
        resource_type=FeaturedResource.ResourceType.MANUSCRIPT,
        source=FeaturedResource.Source.ARCHIVE,
        source_id="archive-2",
        detail_path="/archive/archive-2/",
        access=FeaturedResource.Access.RESTRICTED,
        is_published=True,
    )
    unpublished = FeaturedResource.objects.create(
        title="Draft Resource",
        resource_type=FeaturedResource.ResourceType.EBOOK,
        source=FeaturedResource.Source.CATALOGUE,
        source_id="catalogue-1",
        detail_path="/opac/catalogue-1/",
    )

    published_update = InstitutionalUpdate.objects.create(
        kind=InstitutionalUpdate.Kind.ANNOUNCEMENT,
        title="Archive open day",
        is_published=True,
    )
    future_update = InstitutionalUpdate.objects.create(
        kind=InstitutionalUpdate.Kind.EVENT,
        title="Future event",
        published_at=timezone.now() + timedelta(days=1),
        is_published=True,
    )
    FooterLink.objects.create(
        group=FooterLink.Group.QUICK_LINKS, label="Home", url="/", is_approved=True
    )
    FooterLink.objects.create(
        group=FooterLink.Group.CONNECT,
        label="Unofficial page",
        url="https://example.org",
        is_approved=False,
    )
    return SimpleNamespace(
        homepage=homepage,
        public_resource=public_resource,
        restricted=restricted,
        unpublished=unpublished,
        published_update=published_update,
        future_update=future_update,
    )


@pytest.mark.django_db
def test_homepage_is_public_and_contains_only_approved_content(api_client, public_content):
    response = api_client.get(HOME_URL)

    assert response.status_code == 200
    payload = response.data
    assert payload["language"] == "en"
    assert payload["hero"]["title"] == "A world of knowledge."
    assert payload["hero"]["popularSearches"] == [{"label": "Afaan Oromo", "query": "Afaan Oromo"}]
    assert [card["title"] for card in payload["offers"]["cards"]] == ["Extensive Collection"]
    assert [card["title"] for card in payload["learning"]["cards"]] == ["Discover"]
    assert payload["heritage"]["cards"] == []
    assert [item["slug"] for item in payload["categories"]] == ["ebooks"]
    assert [item["title"] for item in payload["featuredResources"]] == ["Oral History Collection"]
    assert [item["title"] for item in payload["updates"]] == ["Archive open day"]
    assert payload["footer"]["groups"]["quick_links"] == [{"label": "Home", "url": "/", "icon": ""}]
    assert payload["footer"]["groups"]["connect"] == []
    assert payload["membership"]["path"] == "/membership"


@pytest.mark.django_db
def test_unpublished_content_is_not_exposed_to_authenticated_users(api_client, public_content):
    api_client.force_authenticate(user=make_user("website_reader"))
    response = api_client.get(HOME_URL)

    titles = [item["title"] for item in response.data["featuredResources"]]
    assert "Restricted Manuscript" not in titles
    assert "Draft Resource" not in titles
    assert "Future event" not in [item["title"] for item in response.data["updates"]]


@pytest.mark.django_db
def test_language_override_and_fallback(api_client, public_content):
    assert api_client.get(f"{HOME_URL}?lang=om").data["hero"]["title"] == "Addunyaa beekumsaa."
    assert api_client.get(f"{HOME_URL}?lang=zz").data["hero"]["title"] == "A world of knowledge."
    assert api_client.get(HOME_URL, HTTP_ACCEPT_LANGUAGE="am-ET,am;q=0.9").data["language"] == "am"


@pytest.mark.django_db
def test_homepage_without_published_configuration_still_returns_sections(api_client, db):
    ContentSection.objects.create(
        slug="offer", kind=ContentSection.Kind.OFFER, title="What We Offer", is_published=True
    )
    response = api_client.get(HOME_URL)

    assert response.status_code == 200
    assert response.data["hero"]["title"] == ""
    assert response.data["hero"]["popularSearches"] == []
    assert response.data["offers"]["title"] == "What We Offer"
