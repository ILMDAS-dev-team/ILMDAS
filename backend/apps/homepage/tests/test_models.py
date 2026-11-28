"""Model, validator and translation behaviour for website content."""

from __future__ import annotations

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.homepage.models import (
    ContentSection,
    FeaturedResource,
    FooterLink,
    Homepage,
    ResourceCategory,
)
from apps.homepage.translation import localized


@pytest.mark.django_db
def test_localized_text_falls_back_to_base_value():
    homepage = Homepage(
        hero_title="A world of knowledge.",
        translations={"om": {"hero_title": "Addunyaa beekumsaa."}},
    )
    assert localized(homepage, "hero_title", "om") == "Addunyaa beekumsaa."
    assert localized(homepage, "hero_title", "am") == "A world of knowledge."
    assert localized(homepage, "hero_description", "om") == ""


@pytest.mark.django_db
def test_public_links_must_not_point_outside_the_site():
    with pytest.raises(ValidationError):
        FooterLink(label="External", url="javascript:alert(1)").full_clean()
    with pytest.raises(ValidationError):
        Homepage(hero_title="Hero", archive_feature_path="//evil.example").full_clean()
    FooterLink(label="Home", url="/").full_clean()


@pytest.mark.django_db
def test_resource_strings_and_defaults():
    section = ContentSection.objects.create(slug="offer", title="What We Offer")
    assert str(section) == "What We Offer"
    category = ResourceCategory.objects.create(label="E-books", slug="ebooks")
    assert str(category) == "E-books"
    assert category.is_active is False
    resource = FeaturedResource(
        title="Oral history",
        resource_type=FeaturedResource.ResourceType.ORAL_HISTORY,
        source=FeaturedResource.Source.ARCHIVE,
        source_id="object-1",
        detail_path="/archive/object-1/",
    )
    assert str(resource) == "Oral history"
    assert resource.access == FeaturedResource.Access.PUBLIC


@pytest.mark.django_db
def test_only_one_homepage_can_be_published():
    Homepage.objects.create(hero_title="Published", is_published=True)

    with pytest.raises(IntegrityError), transaction.atomic():
        Homepage.objects.create(hero_title="Second published", is_published=True)

    assert Homepage.objects.filter(is_published=True).count() == 1
