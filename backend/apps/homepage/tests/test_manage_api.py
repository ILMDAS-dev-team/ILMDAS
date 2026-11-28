"""Role-guarded content management endpoints stay closed to public visitors."""

from __future__ import annotations

import pytest

from apps.accounts.constants import ROLE_MANAGER
from apps.accounts.testing import make_user
from apps.audit.models import AuditRecord
from apps.homepage.models import Homepage, ResourceCategory

CATEGORIES_URL = "/api/v1/website/manage/categories/"
HOMEPAGE_URL = "/api/v1/website/manage/homepage/"


@pytest.mark.django_db
def test_anonymous_and_member_cannot_read_or_write_content(api_client):
    response = api_client.get(CATEGORIES_URL)
    assert response.status_code in (401, 403)
    assert ResourceCategory.objects.count() == 0

    api_client.force_authenticate(user=make_user("plain_member"))
    denied = api_client.post(CATEGORIES_URL, {"label": "E-books", "slug": "ebooks"})
    assert denied.status_code == 403
    assert ResourceCategory.objects.count() == 0


@pytest.mark.django_db
def test_manager_can_create_content_and_event_is_audited(api_client):
    manager = make_user("content_manager", ROLE_MANAGER)
    api_client.force_authenticate(manager)

    response = api_client.post(
        CATEGORIES_URL,
        {"label": "E-books", "slug": "ebooks", "is_active": True},
        format="json",
    )

    assert response.status_code == 201
    assert ResourceCategory.objects.filter(slug="ebooks").exists()
    assert AuditRecord.objects.filter(
        action="website.content.create", actor=manager, object_type="ResourceCategory"
    ).exists()


@pytest.mark.django_db
def test_manager_can_publish_homepage_and_updated_by_is_set(api_client):
    manager = make_user("homepage_editor", ROLE_MANAGER)
    api_client.force_authenticate(manager)

    response = api_client.post(
        HOMEPAGE_URL,
        {"hero_title": "A world of knowledge.", "is_published": True},
        format="json",
    )

    assert response.status_code == 201
    homepage = Homepage.objects.get()
    assert homepage.updated_by == manager
    assert homepage.is_published is True


@pytest.mark.django_db
def test_invalid_translation_and_unsafe_link_are_rejected(api_client):
    manager = make_user("invalid_editor", ROLE_MANAGER)
    api_client.force_authenticate(manager)

    bad_language = api_client.post(
        CATEGORIES_URL,
        {"label": "Books", "slug": "books", "translations": {"xx": {"label": "Books"}}},
        format="json",
    )
    assert bad_language.status_code == 400
    assert "translations" in bad_language.data["errors"]

    bad_path = api_client.post(
        HOMEPAGE_URL,
        {"hero_title": "Hero", "archive_feature_path": "//evil.example/archive"},
        format="json",
    )
    assert bad_path.status_code == 400
    assert "archive_feature_path" in bad_path.data["errors"]
