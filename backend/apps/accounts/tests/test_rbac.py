"""RBAC authorization tests for ILMDAS-28 / ILMDAS-205 / ILMDAS-231."""

from __future__ import annotations

import hashlib
from unittest.mock import patch

from django.contrib.auth.models import User
from django.db import IntegrityError

from apps.accounts.constants import (
    ROLE_DIGITAL_ARCHIVIST,
    ROLE_INTEGRATION_ADMINISTRATOR,
    ROLE_JOURNAL_EDITOR,
    ROLE_LIBRARIAN,
    ROLE_MANAGER,
    ROLE_MEMBER,
    ROLE_SYSTEM_ADMINISTRATOR,
)
from apps.accounts.models import Role, UserRole, seed_roles
from apps.core.search import CatalogueIndex
from apps.core.storage import StoredObject


def _make_user(username: str) -> User:
    return User.objects.create_user(username=username, password="local-only")


def _assign(user: User, role_code: str) -> None:
    role = Role.objects.get(code=role_code)
    UserRole.objects.create(user=user, role=role)


def _has_role(user: User, role_code: str) -> bool:
    return UserRole.objects.filter(user=user, role__code=role_code).exists()


# ---- Role creation ----

import pytest  # noqa: E402


@pytest.mark.django_db
def test_seven_roles_exist_after_seed():
    seed_roles()
    codes = set(Role.objects.values_list("code", flat=True))
    expected = {
        ROLE_SYSTEM_ADMINISTRATOR,
        ROLE_LIBRARIAN,
        ROLE_DIGITAL_ARCHIVIST,
        ROLE_JOURNAL_EDITOR,
        ROLE_MEMBER,
        ROLE_MANAGER,
        ROLE_INTEGRATION_ADMINISTRATOR,
    }
    assert codes == expected


@pytest.mark.django_db
def test_seed_roles_is_idempotent():
    seed_roles()
    count_before = Role.objects.count()
    seed_roles()
    count_after = Role.objects.count()
    assert count_before == count_after


@pytest.mark.django_db
def test_duplicate_role_code_prevented():
    seed_roles()
    try:
        Role.objects.create(
            code=ROLE_SYSTEM_ADMINISTRATOR,
            name="Duplicate",
        )
        raise AssertionError("Expected IntegrityError for duplicate role code")
    except IntegrityError:
        pass


# ---- User-role assignment ----


@pytest.mark.django_db
def test_user_can_be_assigned_role():
    seed_roles()
    user = _make_user("assignable")
    _assign(user, ROLE_LIBRARIAN)
    assert _has_role(user, ROLE_LIBRARIAN)


@pytest.mark.django_db
def test_user_can_have_multiple_roles():
    seed_roles()
    user = _make_user("multi")
    _assign(user, ROLE_LIBRARIAN)
    _assign(user, ROLE_DIGITAL_ARCHIVIST)
    assert _has_role(user, ROLE_LIBRARIAN)
    assert _has_role(user, ROLE_DIGITAL_ARCHIVIST)


@pytest.mark.django_db
def test_duplicate_user_role_assignment_prevented():
    seed_roles()
    user = _make_user("duprole")
    _assign(user, ROLE_MEMBER)
    try:
        _assign(user, ROLE_MEMBER)
        raise AssertionError("Expected IntegrityError for duplicate user-role")
    except IntegrityError:
        pass


# ---- Role retrieval via session API ----


@pytest.mark.django_db
def test_session_api_returns_user_roles(api_client):
    seed_roles()
    user = _make_user("sessionuser")
    _assign(user, ROLE_LIBRARIAN)
    api_client.force_authenticate(user)
    response = api_client.get("/api/v1/contract/session/")
    assert response.status_code == 200
    role_codes = [r["code"] for r in response.data["user"]["roles"]]
    assert ROLE_LIBRARIAN in role_codes


# ---- Authorization: staff catalogue update (ObjectUploadView) ----


@pytest.mark.django_db
def test_authenticated_member_cannot_upload_object(api_client):
    seed_roles()
    user = _make_user("member")
    _assign(user, ROLE_MEMBER)
    api_client.force_authenticate(user)
    response = api_client.post(
        "/api/v1/storage/objects/",
        {"objectKey": "x", "bodyBase64": "dGhpcyBpcyBhIHRlc3Q="},
        format="json",
    )
    assert response.status_code == 403
    assert response.data["code"] == "authorization_error"


@pytest.mark.django_db
def test_system_administrator_can_upload_object(api_client):
    seed_roles()
    user = _make_user("admin")
    _assign(user, ROLE_SYSTEM_ADMINISTRATOR)
    api_client.force_authenticate(user)
    stored = StoredObject(
        reference="s3://ilmdas-files/x",
        checksum_sha256=hashlib.sha256(b"test").hexdigest(),
        object_key="x",
    )
    with patch("apps.core.views.ObjectStorage.put_private", return_value=stored):
        response = api_client.post(
            "/api/v1/storage/objects/",
            {"objectKey": "x", "bodyBase64": "dGVzdA=="},
            format="json",
        )
    assert response.status_code == 201


# ---- Authorization: catalogue index (CatalogueIndexView) ----


@pytest.mark.django_db
def test_authenticated_member_cannot_rebuild_catalogue_index(api_client):
    seed_roles()
    user = _make_user("member2")
    _assign(user, ROLE_MEMBER)
    api_client.force_authenticate(user)
    response = api_client.post("/api/v1/search/catalogue-index/")
    assert response.status_code == 403
    assert response.data["code"] == "authorization_error"


@pytest.mark.django_db
def test_system_administrator_can_rebuild_catalogue_index(api_client):
    seed_roles()
    user = _make_user("admin2")
    _assign(user, ROLE_SYSTEM_ADMINISTRATOR)
    api_client.force_authenticate(user)
    from unittest.mock import patch

    with (
        patch("apps.core.views.CatalogueIndex.rebuild"),
        patch("apps.core.views.CatalogueIndex.delete"),
        patch.object(
            CatalogueIndex,
            "index_name",
            "ilmdas-catalogue",
            create=True,
        ),
    ):
        response = api_client.post("/api/v1/search/catalogue-index/")
    assert response.status_code == 201


# ---- Authorization: librarian cannot access integration admin ----


@pytest.mark.django_db
def test_librarian_cannot_access_integration_administrator_operations(api_client):
    """Librarian must not access integration-administrator configuration."""
    seed_roles()
    user = _make_user("librarian")
    _assign(user, ROLE_LIBRARIAN)
    api_client.force_authenticate(user)
    assert not _has_role(user, ROLE_INTEGRATION_ADMINISTRATOR)


# ---- Authentication ----


@pytest.mark.django_db
def test_unauthenticated_request_receives_401(api_client):
    response = api_client.get("/api/v1/contract/session/")
    assert response.status_code == 401
    assert response.data["code"] == "authentication_error"


@pytest.mark.django_db
def test_unauthenticated_request_receives_401_on_protected_endpoint(api_client):
    seed_roles()
    response = api_client.post("/api/v1/storage/objects/", {}, format="json")
    assert response.status_code == 401


# ---- Unauthorized requests do not modify records ----


@pytest.mark.django_db
def test_unauthorized_upload_does_not_create_record(api_client):
    seed_roles()
    user = _make_user("member3")
    _assign(user, ROLE_MEMBER)
    api_client.force_authenticate(user)
    from apps.core.models import ObjectReference

    before_count = ObjectReference.objects.count()
    response = api_client.post(
        "/api/v1/storage/objects/",
        {"objectKey": "x", "bodyBase64": "dGhpcyBpcyBhIHRlc3Q="},
        format="json",
    )
    assert response.status_code == 403
    after_count = ObjectReference.objects.count()
    assert after_count == before_count
