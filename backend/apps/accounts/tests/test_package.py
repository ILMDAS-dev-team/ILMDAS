"""Tests for accounts, custom user model, roles, authentication, and throttling."""

from __future__ import annotations

import logging

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import UNUSABLE_PASSWORD_PREFIX, make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from rest_framework.test import APIClient

from apps.accounts.constants import (
    ROLE_DIGITAL_ARCHIVIST,
    ROLE_GUEST,
    ROLE_LIBRARIAN,
    ROLE_MEMBER,
    ROLE_SYSTEM_ADMINISTRATOR,
)
from apps.accounts.models import User, UserAccount, UserAccountStatus, seed_roles
from apps.accounts.testing import make_user
from apps.audit.models import AuditRecord

TEST_PASSWORD = "Test@123456!"  # pragma: allowlist secret
CHANGED_PASSWORD = "ChangedSecret@123456!"  # pragma: allowlist secret
SET_PASSWORD_VALUE = "NewSecretViaSet@123456!"  # pragma: allowlist secret
PARTIAL_UPDATE_PASSWORD = "ChangedPassword123!"  # pragma: allowlist secret
WRONG_PASSWORD = "IncorrectPassword!"  # pragma: allowlist secret


def test_accounts_package_imports():
    import apps.accounts as app

    assert app.__name__ == "apps.accounts"


@pytest.mark.django_db
def test_custom_user_model_defined_and_role_properties():
    user_model = get_user_model()
    assert user_model is User

    guest = make_user("guest_test")
    assert guest.is_guest is True
    assert guest.is_member is False
    assert guest.is_library_staff is False
    assert guest.is_archivist is False
    assert guest.is_administrator is False

    member = make_user("member_test", ROLE_MEMBER)
    assert member.is_member is True
    assert member.is_guest is False

    staff = make_user("staff_test", ROLE_LIBRARIAN)
    assert staff.is_library_staff is True
    assert staff.is_archivist is False
    assert staff.is_member is False  # staff become members only through a membership

    archivist = make_user("archivist_test", ROLE_DIGITAL_ARCHIVIST)
    assert archivist.is_archivist is True
    assert archivist.is_library_staff is False

    admin = make_user("admin_test", ROLE_SYSTEM_ADMINISTRATOR)
    assert admin.is_administrator is True
    assert admin.is_library_staff is True
    assert admin.is_archivist is True


@pytest.mark.django_db
def test_new_account_gets_guest_role_once():
    seed_roles()
    user = User.objects.create_user(username="fresh", password=TEST_PASSWORD)
    user.save()  # saving again must not add a second guest role
    assert list(user.user_roles.values_list("role__code", flat=True)) == [ROLE_GUEST]


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
    validate_password(TEST_PASSWORD)


def test_basic_auth_removed_from_defaults():
    from django.conf import settings

    classes = settings.REST_FRAMEWORK.get("DEFAULT_AUTHENTICATION_CLASSES", [])
    assert "rest_framework.authentication.BasicAuthentication" not in classes
    assert "rest_framework.authentication.SessionAuthentication" in classes


@pytest.mark.django_db
def test_legacy_pbkdf2_hash_still_verifies_and_is_upgraded_to_argon2():
    """SRS FR-SEC-002 (bcrypt/Argon2): older PBKDF2 hashes keep working and upgrade on login."""
    user = UserAccount.objects.create_user(username="legacy_hash", password=TEST_PASSWORD)
    user.password = make_password(TEST_PASSWORD, hasher="pbkdf2_sha256")
    user.save()
    assert user.password.startswith("pbkdf2_sha256$")

    assert user.check_password(TEST_PASSWORD) is True
    user.refresh_from_db()
    assert user.password.startswith("argon2$")


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
    assert stored_password.startswith("argon2$")

    # Database row-level inspection: prove raw password is absent from every column in the stored row
    table_name = connection.ops.quote_name(User._meta.db_table)
    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT * FROM {table_name} WHERE username = %s",  # noqa: S608
            [account.username],
        )
        row = cursor.fetchone()
        assert row is not None
        for col_value in row:
            if col_value is not None:
                assert raw_password not in str(col_value)

    # One-way verification
    assert account.check_password(raw_password) is True
    assert account.check_password(WRONG_PASSWORD) is False


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
    assert direct_user.password.startswith("argon2$")
    assert direct_user.check_password(TEST_PASSWORD) is True

    # 2. Password change via direct assignment
    direct_user.password = CHANGED_PASSWORD
    direct_user.save()
    assert CHANGED_PASSWORD not in direct_user.password
    assert direct_user.password.startswith("argon2$")
    assert direct_user.check_password(CHANGED_PASSWORD) is True
    assert direct_user.check_password(TEST_PASSWORD) is False

    # 3. Password change via set_password
    direct_user.set_password(SET_PASSWORD_VALUE)
    direct_user.save()
    assert SET_PASSWORD_VALUE not in direct_user.password
    assert direct_user.check_password(SET_PASSWORD_VALUE) is True
    assert direct_user.check_password(CHANGED_PASSWORD) is False

    # 4. Password change with update_fields=["password"]
    direct_user.password = PARTIAL_UPDATE_PASSWORD
    direct_user.save(update_fields=["password"])
    direct_user.refresh_from_db()
    assert PARTIAL_UPDATE_PASSWORD not in direct_user.password
    assert direct_user.password.startswith("argon2$")
    assert direct_user.check_password(PARTIAL_UPDATE_PASSWORD) is True
    assert direct_user.check_password(SET_PASSWORD_VALUE) is False


@pytest.mark.django_db
def test_unusable_password_marker_is_preserved_on_later_saves_sec_01():
    """A password disabled with set_password(None) must never become usable again."""
    account = UserAccount.objects.create_user(username="unusable_password_user")
    marker = account.password
    assert marker.startswith(UNUSABLE_PASSWORD_PREFIX)

    account.activate()
    account.refresh_from_db()
    assert account.password == marker

    account.save()
    account.refresh_from_db()
    assert account.password == marker
    assert account.check_password(marker) is False
    assert account.check_password(TEST_PASSWORD) is False


@pytest.mark.django_db
def test_raw_password_is_persisted_with_partial_update_fields_sec_01():
    """Hashing must reach the database even when update_fields omits the password."""
    account = UserAccount.objects.create_user(
        username="partial_update_user", password=TEST_PASSWORD
    )
    account.password = PARTIAL_UPDATE_PASSWORD
    account.status = UserAccountStatus.INACTIVE

    account.save(update_fields=["status"])
    account.refresh_from_db()

    assert account.password.startswith("argon2$")
    assert account.check_password(PARTIAL_UPDATE_PASSWORD) is True
    assert account.check_password(TEST_PASSWORD) is False
    assert account.status == UserAccountStatus.INACTIVE


@pytest.mark.django_db
def test_password_is_never_logged_during_create_or_change(caplog):
    """API / Backend Notes: Use Django's password hasher or an equivalent approved one-way algorithm."""
    with caplog.at_level(logging.DEBUG):
        user = UserAccount.objects.create_user(
            username="unlogged_user_1",
            password=TEST_PASSWORD,
        )
        direct = User(
            username="unlogged_user_2",
            password=TEST_PASSWORD,
        )
        direct.save()
        user.password = CHANGED_PASSWORD
        user.save()
        direct.set_password(SET_PASSWORD_VALUE)
        direct.save()

    assert TEST_PASSWORD not in caplog.text
    assert CHANGED_PASSWORD not in caplog.text
    assert SET_PASSWORD_VALUE not in caplog.text
    assert TEST_PASSWORD not in str(user)
    assert TEST_PASSWORD not in repr(user)


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

    # Invalid status value fails validation on full_clean, save, and DB update
    account.status = "invalid_status_value"
    with pytest.raises(ValidationError):
        account.full_clean()
    with pytest.raises(ValidationError):
        account.save()
    with pytest.raises(IntegrityError), transaction.atomic():
        UserAccount.objects.filter(pk=account.pk).update(status="invalid_status_value")


@pytest.mark.django_db
def test_hash_from_another_default_hasher_is_kept_on_save():
    """A stored bcrypt_sha256 hash must not be re-hashed as if it were a plain password."""
    user = UserAccount.objects.create_user(username="bcrypt_user", password=TEST_PASSWORD)
    bcrypt_hash = "bcrypt_sha256$$2b$12$" + "a" * 53  # format only; never verified here
    UserAccount.objects.filter(pk=user.pk).update(password=bcrypt_hash)
    user.refresh_from_db()

    user.status = UserAccountStatus.SUSPENDED
    user.save()
    user.refresh_from_db()
    assert user.password == bcrypt_hash
