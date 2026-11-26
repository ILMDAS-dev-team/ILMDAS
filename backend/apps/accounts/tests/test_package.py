"""Tests for accounts, custom user model, roles, authentication, and throttling."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from rest_framework.test import APIClient

from apps.accounts.constants import (
    ROLE_DIGITAL_ARCHIVIST,
    ROLE_LIBRARIAN,
    ROLE_MEMBER,
    ROLE_SYSTEM_ADMINISTRATOR,
)
from apps.accounts.models import User, UserAccount, UserAccountStatus, seed_roles
from apps.accounts.testing import make_user
from apps.audit.models import AuditRecord

TEST_PASSWORD = "Test@123456!"  # pragma: allowlist secret


def test_accounts_package_imports():
    import apps.accounts as app

    assert app.__name__ == "apps.accounts"


@pytest.mark.django_db
def test_custom_user_model_defined_and_role_properties():
    user_model = get_user_model()
    assert user_model is User

    member = make_user("member_test")
    assert member.is_member is True
    assert member.is_library_staff is False
    assert member.is_archivist is False
    assert member.is_administrator is False

    staff = make_user("staff_test", ROLE_LIBRARIAN)
    assert staff.is_library_staff is True
    assert staff.is_archivist is False
    assert staff.is_member is True  # every account is also a member

    archivist = make_user("archivist_test", ROLE_DIGITAL_ARCHIVIST)
    assert archivist.is_archivist is True
    assert archivist.is_library_staff is False

    admin = make_user("admin_test", ROLE_SYSTEM_ADMINISTRATOR)
    assert admin.is_administrator is True
    assert admin.is_library_staff is True
    assert admin.is_archivist is True


@pytest.mark.django_db
def test_new_account_gets_member_role_once():
    seed_roles()
    user = User.objects.create_user(username="fresh", password=TEST_PASSWORD)
    user.save()  # saving again must not add a second member role
    assert list(user.user_roles.values_list("role__code", flat=True)) == [ROLE_MEMBER]


@pytest.mark.django_db
def test_login_success_and_audit():
    user = make_user("login_user", ROLE_LIBRARIAN)
    client = APIClient()
    response = client.post(
        "/api/v1/auth/login/",
        {"username": "login_user", "password": TEST_PASSWORD},
        format="json",
    )
    assert response.status_code == 200
    assert response.data["username"] == "login_user"
    assert {"code": ROLE_LIBRARIAN, "name": "Librarian"} in response.data["roles"]
    assert response.data["isStaff"] is True

    audit = AuditRecord.objects.filter(action="auth.login", actor=user).first()
    assert audit is not None
    assert audit.actor_username == "login_user"


@pytest.mark.django_db
def test_login_failure_and_audit():
    User.objects.create_user(username="target_user", password=TEST_PASSWORD)
    client = APIClient()
    response = client.post(
        "/api/v1/auth/login/",
        {"username": "target_user", "password": "WrongPassword!"},  # pragma: allowlist secret
        format="json",
    )
    assert response.status_code == 401

    audit = AuditRecord.objects.filter(
        action="auth.login.failed", actor_username="target_user"
    ).first()
    assert audit is not None


@pytest.mark.django_db
def test_logout_and_session_endpoints():
    user = make_user("session_user", ROLE_DIGITAL_ARCHIVIST)
    client = APIClient()
    client.force_authenticate(user)

    session_resp = client.get("/api/v1/auth/me/")
    assert session_resp.status_code == 200
    assert session_resp.data["username"] == "session_user"
    assert session_resp.data["isArchivist"] is True
    assert {"code": ROLE_DIGITAL_ARCHIVIST, "name": "Digital Archivist"} in session_resp.data[
        "roles"
    ]

    logout_resp = client.post("/api/v1/auth/logout/")
    assert logout_resp.status_code == 200
    assert logout_resp.data["status"] == "logged_out"
    assert AuditRecord.objects.filter(action="auth.logout", actor=user).exists()


# --- User Account Model and Secure Password Hashing (FR-SEC-002, SEC-01) ---


@pytest.mark.django_db
def test_user_account_entity_fields_and_traceability_fr_sec_002():
    """Verify UserAccount entity fields: stable id, username, password hash, status, timestamps."""
    assert UserAccount is User

    account = UserAccount.objects.create_user(
        username="librarian_01",
        password=TEST_PASSWORD,
    )
    assert account.id is not None
    assert account.username == "librarian_01"
    assert account.status == UserAccountStatus.ACTIVE
    assert account.created_at is not None
    assert account.created_time == account.created_at
    assert account.last_login is None
    assert account.last_login_time is None
    assert account.password_hash == account.password
    assert TEST_PASSWORD not in account.password_hash


@pytest.mark.django_db
def test_password_stored_as_secure_one_way_hash_not_raw_password_sec_01():
    """Acceptance criteria: A created account stores a hash, not the password."""
    raw_password = TEST_PASSWORD
    account = UserAccount.objects.create_user(
        username="hashing_target",
        password=raw_password,
    )

    # Directly inspect database stored string
    stored_password = (
        UserAccount.objects.filter(username="hashing_target")
        .values_list("password", flat=True)
        .first()
    )
    assert stored_password is not None
    assert stored_password != raw_password
    assert raw_password not in stored_password
    assert stored_password.startswith("pbkdf2_sha256$")

    # One-way verification
    assert account.check_password(raw_password) is True
    assert account.check_password("IncorrectPassword!") is False


@pytest.mark.django_db
def test_password_hashing_on_create_and_change_sec_01():
    """Scope of work: Password hashing on create and change."""
    # 1. Direct instantiation and save
    direct_user = User(
        username="direct_user",
        password=TEST_PASSWORD,
    )
    direct_user.save()
    assert TEST_PASSWORD not in direct_user.password
    assert direct_user.password.startswith("pbkdf2_sha256$")
    assert direct_user.check_password(TEST_PASSWORD) is True

    # 2. Password change via direct assignment
    direct_user.password = "ChangedSecret@123456!"  # pragma: allowlist secret
    direct_user.save()
    assert "ChangedSecret@123456!" not in direct_user.password
    assert direct_user.password.startswith("pbkdf2_sha256$")
    assert direct_user.check_password("ChangedSecret@123456!") is True
    assert direct_user.check_password(TEST_PASSWORD) is False

    # 3. Password change via set_password
    direct_user.set_password("NewSecretViaSet@123456!")
    direct_user.save()
    assert "NewSecretViaSet@123456!" not in direct_user.password
    assert direct_user.check_password("NewSecretViaSet@123456!") is True
    assert direct_user.check_password("ChangedSecret@123456!") is False


@pytest.mark.django_db
def test_duplicate_usernames_are_rejected_sec_01():
    """Acceptance criteria: Duplicate usernames are rejected."""
    UserAccount.objects.create_user(
        username="unique_username",
        password=TEST_PASSWORD,
    )

    with pytest.raises(IntegrityError):
        UserAccount.objects.create_user(
            username="unique_username",
            password="DifferentPassword456!",  # pragma: allowlist secret
        )


@pytest.mark.django_db
def test_status_lifecycle_values_activation_and_deactivation_fr_sec_002():
    """Acceptance criteria: Status accepts the lifecycle values used by activation and deactivation."""
    # Verify expected lifecycle constants
    assert UserAccountStatus.PENDING == "pending"
    assert UserAccountStatus.ACTIVE == "active"
    assert UserAccountStatus.INACTIVE == "inactive"
    assert UserAccountStatus.SUSPENDED == "suspended"
    assert UserAccountStatus.DEACTIVATED == "deactivated"

    # Default is ACTIVE and is_active is True
    account = UserAccount.objects.create_user(
        username="lifecycle_user",
        password=TEST_PASSWORD,
    )
    assert account.status == UserAccountStatus.ACTIVE
    assert account.is_active is True

    # Deactivation lifecycle
    account.deactivate()
    account.refresh_from_db()
    assert account.status == UserAccountStatus.INACTIVE
    assert account.is_active is False

    # Activation lifecycle
    account.activate()
    account.refresh_from_db()
    assert account.status == UserAccountStatus.ACTIVE
    assert account.is_active is True

    # Suspension lifecycle
    account.suspend()
    account.refresh_from_db()
    assert account.status == UserAccountStatus.SUSPENDED
    assert account.is_active is False

    # Other lifecycle values
    for lifecycle_status in (UserAccountStatus.PENDING, UserAccountStatus.DEACTIVATED):
        account.status = lifecycle_status
        account.save()
        account.refresh_from_db()
        assert account.status == lifecycle_status
        assert account.is_active is False

    # Invalid status value fails validation on full_clean
    account.status = "invalid_status_value"
    with pytest.raises(ValidationError):
        account.full_clean()
