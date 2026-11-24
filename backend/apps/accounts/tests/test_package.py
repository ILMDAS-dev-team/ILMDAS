"""Tests for accounts, custom user model, roles, authentication, and throttling."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from rest_framework.test import APIClient

from apps.accounts.models import Role, User, UserAccount, UserAccountStatus
from apps.audit.models import AuditRecord


def test_accounts_package_imports():
    import apps.accounts as app

    assert app.__name__ == "apps.accounts"


@pytest.mark.django_db
def test_custom_user_model_defined_and_role_properties():
    user_model = get_user_model()
    assert user_model is User

    member = user_model.objects.create_user(username="member_test", password="Test@123456!")
    assert member.role == Role.MEMBER
    assert member.is_member is True
    assert member.is_library_staff is False
    assert member.is_archivist is False
    assert member.is_administrator is False

    staff = user_model.objects.create_user(
        username="staff_test", password="Test@123456!", role=Role.LIBRARY_STAFF
    )
    assert staff.is_library_staff is True
    assert staff.is_member is False

    archivist = user_model.objects.create_user(
        username="archivist_test", password="Test@123456!", role=Role.ARCHIVIST
    )
    assert archivist.is_archivist is True
    assert archivist.is_member is False

    admin = user_model.objects.create_user(
        username="admin_test", password="Test@123456!", role=Role.ADMINISTRATOR
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
    validate_password("Test@123456!")


def test_basic_auth_removed_from_defaults():
    from django.conf import settings

    classes = settings.REST_FRAMEWORK.get("DEFAULT_AUTHENTICATION_CLASSES", [])
    assert "rest_framework.authentication.BasicAuthentication" not in classes
    assert "rest_framework.authentication.SessionAuthentication" in classes


@pytest.mark.django_db
def test_login_success_and_audit():
    user = User.objects.create_user(
        username="login_user", password="Test@123456!", role=Role.LIBRARY_STAFF
    )
    client = APIClient()
    response = client.post(
        "/api/v1/auth/login/",
        {"username": "login_user", "password": "Test@123456!"},
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
    User.objects.create_user(username="target_user", password="Test@123456!")
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
        username="session_user", password="Test@123456!", role=Role.ARCHIVIST
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


# --- User Account Model and Secure Password Hashing (FR-SEC-002, SEC-01) ---


@pytest.mark.django_db
def test_user_account_entity_fields_and_traceability_fr_sec_002():
    """Verify UserAccount entity fields: stable id, username, password hash, status, timestamps."""
    assert UserAccount is User

    account = UserAccount.objects.create_user(
        username="librarian_01",
        password="Test@123456!",
    )
    assert account.id is not None
    assert account.username == "librarian_01"
    assert account.status == UserAccountStatus.ACTIVE
    assert account.created_at is not None
    assert account.created_time == account.created_at
    assert account.last_login is None
    assert account.last_login_time is None
    assert account.password_hash == account.password
    assert "Test@123456!" not in account.password_hash


@pytest.mark.django_db
def test_password_stored_as_secure_one_way_hash_not_raw_password_sec_01():
    """Acceptance criteria: A created account stores a hash, not the password (Test ref SEC-01).

    Proves the raw password is absent from the stored database row.
    """
    raw_password = "Test@123456!"

    # 1. Created via create_user
    account1 = UserAccount.objects.create_user(
        username="hashing_target_1",
        password=raw_password,
    )
    # 2. Created via UserAccount.objects.create
    account2 = UserAccount.objects.create(
        username="hashing_target_2",
        password=raw_password,
    )
    # 3. Created via User(...).save()
    account3 = User(
        username="hashing_target_3",
        password=raw_password,
    )
    account3.save()

    for account in (account1, account2, account3):
        # ORM-level inspection: stores hash starting with approved hasher algorithm
        stored_password = (
            UserAccount.objects.filter(username=account.username)
            .values_list("password", flat=True)
            .first()
        )
        assert stored_password is not None
        assert stored_password != raw_password
        assert raw_password not in stored_password
        assert stored_password.startswith("pbkdf2_sha256$")

        # Database row-level inspection: prove raw password is absent from every column in the stored row
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM accounts_user WHERE username = %s",
                [account.username],
            )
            row = cursor.fetchone()
            assert row is not None
            for col_value in row:
                if col_value is not None:
                    assert raw_password not in str(col_value)

        # Cryptographic verification: one-way verification succeeds on exact password and fails on incorrect
        assert account.check_password(raw_password) is True
        assert account.check_password("IncorrectPassword!") is False


@pytest.mark.django_db
def test_password_hashing_on_create_and_change_sec_01():
    """Scope of work: Password hashing on create and change."""
    # 1. Direct instantiation and save hashes password
    direct_user = User(
        username="direct_user",
        password="Test@123456!",
    )
    direct_user.save()
    assert "Test@123456!" not in direct_user.password
    assert direct_user.password.startswith("pbkdf2_sha256$")
    assert direct_user.check_password("Test@123456!") is True

    # 2. UserAccount.objects.create hashes password
    created_user = UserAccount.objects.create(
        username="created_account_user",
        password="Test@123456!",
    )
    assert "Test@123456!" not in created_user.password
    assert created_user.password.startswith("pbkdf2_sha256$")
    assert created_user.check_password("Test@123456!") is True

    # 3. Password change via direct assignment
    old_hash = direct_user.password
    direct_user.password = "Test@123456!"
    direct_user.save()
    assert "Test@123456!" not in direct_user.password
    assert direct_user.password.startswith("pbkdf2_sha256$")
    assert direct_user.password != old_hash
    assert direct_user.check_password("Test@123456!") is True

    # 4. Password change via set_password
    set_pwd_hash = direct_user.password
    direct_user.set_password("Test@123456!")
    direct_user.save()
    assert "Test@123456!" not in direct_user.password
    assert direct_user.password.startswith("pbkdf2_sha256$")
    assert direct_user.password != set_pwd_hash
    assert direct_user.check_password("Test@123456!") is True

    # 5. Password change with update_fields=["password"]
    direct_user.password = "Test@123456!"
    direct_user.save(update_fields=["password"])
    direct_user.refresh_from_db()
    assert "Test@123456!" not in direct_user.password
    assert direct_user.password.startswith("pbkdf2_sha256$")
    assert direct_user.check_password("Test@123456!") is True

    # 6. Database raw query verification: raw password never in database row
    stored_password = (
        UserAccount.objects.filter(username="direct_user")
        .values_list("password", flat=True)
        .first()
    )
    assert stored_password is not None
    assert "Test@123456!" not in stored_password
    assert stored_password.startswith("pbkdf2_sha256$")


@pytest.mark.django_db
def test_password_is_never_logged_during_create_or_change(caplog):
    """API / Backend Notes: Use Django's password hasher or an equivalent approved one-way algorithm. Do not log the password."""
    import logging

    with caplog.at_level(logging.DEBUG):
        # 1. Create via create_user
        user = UserAccount.objects.create_user(
            username="unlogged_user_1",
            password="Test@123456!",
        )

        # 2. Create via direct save
        direct = User(
            username="unlogged_user_2",
            password="Test@123456!",
        )
        direct.save()

        # 3. Create via Model.objects.create
        created = UserAccount.objects.create(
            username="unlogged_user_3",
            password="Test@123456!",
        )

        # 4. Password change via direct assignment
        user.password = "Test@123456!"
        user.save()

        # 5. Password change via set_password
        created.set_password("Test@123456!")
        created.save()

    # Verify that the plaintext password NEVER appeared in any captured log stream
    assert "Test@123456!" not in caplog.text
    # Verify that user string representation does not expose password
    assert "Test@123456!" not in str(user)
    assert "Test@123456!" not in repr(user)


@pytest.mark.django_db
def test_duplicate_usernames_are_rejected_sec_01():
    """Acceptance criteria: Duplicate usernames are rejected (Test ref SEC-01).

    Covers uniqueness constraint enforcement across all persistence paths.
    """
    UserAccount.objects.create_user(
        username="unique_username",
        password="Test@123456!",
    )

    # 1. Duplicate rejected via create_user
    with pytest.raises(IntegrityError), transaction.atomic():
        UserAccount.objects.create_user(
            username="unique_username",
            password="Test@123456!",
        )

    # 2. Duplicate rejected via objects.create
    with pytest.raises(IntegrityError), transaction.atomic():
        UserAccount.objects.create(
            username="unique_username",
            password="Test@123456!",
        )

    # 3. Duplicate rejected via direct instantiation + save()
    dup_save = User(
        username="unique_username",
        password="Test@123456!",
    )
    with pytest.raises(IntegrityError), transaction.atomic():
        dup_save.save()

    # 4. Duplicate rejected via model validation full_clean()
    dup_clean = User(
        username="unique_username",
        password="Test@123456!",
    )
    with pytest.raises(ValidationError):
        dup_clean.full_clean()

    # 5. Duplicate rejected on updating existing user to an already taken username
    second_user = UserAccount.objects.create_user(
        username="second_user",
        password="Test@123456!",
    )
    second_user.username = "unique_username"
    with pytest.raises(IntegrityError), transaction.atomic():
        second_user.save()


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
        password="Test@123456!",
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

    # Invalid status value fails validation on clean, full_clean, and save
    account.status = "invalid_status_value"
    with pytest.raises(ValidationError):
        account.clean()
    with pytest.raises(ValidationError):
        account.full_clean()
    with pytest.raises(ValidationError):
        account.save()


@pytest.mark.django_db
def test_unknown_status_is_rejected_on_create_and_update_sec_01():
    """Acceptance criteria: An unknown status is rejected on create, update, clean, and full_clean."""
    unknown_statuses = ["unknown", "archived", "deleted", "banned", "ACTIVE_UPPER", ""]

    # 1. Rejected on direct instantiation + save
    for bad_status in unknown_statuses:
        user = User(
            username=f"bad_init_{bad_status or 'empty'}",
            password="Test@123456!",
            status=bad_status,
        )
        with pytest.raises(ValidationError):
            user.save()

    # 2. Rejected on UserAccount.objects.create
    for bad_status in unknown_statuses:
        with pytest.raises(ValidationError):
            UserAccount.objects.create(
                username=f"bad_create_{bad_status or 'empty'}",
                password="Test@123456!",
                status=bad_status,
            )

    # 3. Rejected on UserAccount.objects.create_user
    for bad_status in unknown_statuses:
        with pytest.raises(ValidationError):
            UserAccount.objects.create_user(
                username=f"bad_create_user_{bad_status or 'empty'}",
                password="Test@123456!",
                status=bad_status,
            )

    # 4. Rejected on update/modification of existing user
    existing_user = UserAccount.objects.create_user(
        username="existing_status_target",
        password="Test@123456!",
    )
    for bad_status in unknown_statuses:
        existing_user.status = bad_status
        with pytest.raises(ValidationError):
            existing_user.save()
        with pytest.raises(ValidationError):
            existing_user.clean()
        with pytest.raises(ValidationError):
            existing_user.full_clean()

    # Verify existing user remained ACTIVE in database
    existing_user.refresh_from_db()
    assert existing_user.status == UserAccountStatus.ACTIVE
