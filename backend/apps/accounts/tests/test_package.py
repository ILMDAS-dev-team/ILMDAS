"""Tests for accounts, custom user model, roles, authentication, and throttling."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.accounts.models import Role, User
from apps.audit.models import AuditRecord


def test_accounts_package_imports():
    import apps.accounts as app

    assert app.__name__ == "apps.accounts"


@pytest.mark.django_db
def test_custom_user_model_defined_and_role_properties():
    user_model = get_user_model()
    assert user_model is User

    member = user_model.objects.create_user(username="member_test", password="ValidPassword123!")
    assert member.role == Role.MEMBER
    assert member.is_member is True
    assert member.is_library_staff is False
    assert member.is_archivist is False
    assert member.is_administrator is False

    staff = user_model.objects.create_user(
        username="staff_test", password="ValidPassword123!", role=Role.LIBRARY_STAFF
    )
    assert staff.is_library_staff is True
    assert staff.is_member is False

    archivist = user_model.objects.create_user(
        username="archivist_test", password="ValidPassword123!", role=Role.ARCHIVIST
    )
    assert archivist.is_archivist is True
    assert archivist.is_member is False

    admin = user_model.objects.create_user(
        username="admin_test", password="ValidPassword123!", role=Role.ADMINISTRATOR
    )
    assert admin.is_administrator is True
    assert admin.is_library_staff is True
    assert admin.is_archivist is True


def test_password_validators_configured_and_enforce_policy():
    # Passwords shorter than 12 chars should fail
    with pytest.raises(ValidationError):
        validate_password("Short1!")

    # Entirely numeric passwords should fail
    with pytest.raises(ValidationError):
        validate_password("123456789012")

    # Common passwords should fail
    with pytest.raises(ValidationError):
        validate_password("password123456")

    # Strong password should pass
    validate_password("Ethiopia@AddisAbaba2026Secure!")


def test_basic_auth_removed_from_defaults():
    from django.conf import settings

    classes = settings.REST_FRAMEWORK.get("DEFAULT_AUTHENTICATION_CLASSES", [])
    assert "rest_framework.authentication.BasicAuthentication" not in classes
    assert "rest_framework.authentication.SessionAuthentication" in classes


@pytest.mark.django_db
def test_login_success_and_audit():
    user = User.objects.create_user(
        username="login_user", password="ValidPassword123!", role=Role.LIBRARY_STAFF
    )
    client = APIClient()
    response = client.post(
        "/api/v1/auth/login/",
        {"username": "login_user", "password": "ValidPassword123!"},
        format="json",
    )
    assert response.status_code == 200
    assert response.data["username"] == "login_user"
    assert response.data["role"] == "staff"
    assert response.data["isStaff"] is True

    audit = AuditRecord.objects.filter(action="auth.login", actor=user).first()
    assert audit is not None
    assert audit.actor_username == "login_user"


@pytest.mark.django_db
def test_login_failure_and_audit():
    User.objects.create_user(username="target_user", password="ValidPassword123!")
    client = APIClient()
    response = client.post(
        "/api/v1/auth/login/",
        {"username": "target_user", "password": "WrongPassword!"},
        format="json",
    )
    assert response.status_code == 401

    audit = AuditRecord.objects.filter(
        action="auth.login.failed", actor_username="target_user"
    ).first()
    assert audit is not None


@pytest.mark.django_db
def test_logout_and_session_endpoints():
    user = User.objects.create_user(
        username="session_user", password="ValidPassword123!", role=Role.ARCHIVIST
    )
    client = APIClient()
    client.force_authenticate(user)

    session_resp = client.get("/api/v1/auth/session/")
    assert session_resp.status_code == 200
    assert session_resp.data["username"] == "session_user"
    assert session_resp.data["isArchivist"] is True

    logout_resp = client.post("/api/v1/auth/logout/")
    assert logout_resp.status_code == 200
    assert logout_resp.data["status"] == "logged_out"
    assert AuditRecord.objects.filter(action="auth.logout", actor=user).exists()
