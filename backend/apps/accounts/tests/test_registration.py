"""Staff registration (ILMDAS-551) and self-registration with email verification (ILMDAS-552)."""

from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse

import pytest
from django.core import mail

from apps.accounts.constants import (
    ROLE_GUEST,
    ROLE_LIBRARIAN,
    ROLE_MANAGER,
    ROLE_SYSTEM_ADMINISTRATOR,
)
from apps.accounts.models import User, UserAccountStatus
from apps.accounts.serializers import DUPLICATE_ACCOUNT_MESSAGE
from apps.accounts.testing import make_user
from apps.accounts.throttling import RegistrationRateThrottle
from apps.accounts.tokens import email_verification_tokens, staff_invite_tokens
from apps.audit.models import AuditRecord

STRONG_PASSWORD = "Irreecha-Lib-2026!"  # pragma: allowlist secret
OTHER_STRONG_PASSWORD = "Gadaa-Archive-2026!"  # pragma: allowlist secret
WEAK_PASSWORD = "short"  # pragma: allowlist secret


def _link_params(message) -> dict[str, str]:
    """The uid and token from the link in an email."""
    match = re.search(r"https?://\S+", message.body)
    assert match is not None, "the email has no link"
    query = parse_qs(urlparse(match.group(0)).query)
    return {"uid": query["uid"][0], "token": query["token"][0]}


def _roles(user: User) -> set[str]:
    return set(user.user_roles.values_list("role__code", flat=True))


def _actions() -> list[str]:
    return list(AuditRecord.objects.order_by("id").values_list("action", flat=True))


def _registration(**overrides) -> dict:
    data = {
        "username": "chaltu",
        "email": "chaltu@example.org",
        "first_name": "Chaltu",
        "last_name": "Bekele",
        "password": STRONG_PASSWORD,
        "accept_terms": True,
    }
    data.update(overrides)
    return data


# ---- Staff registration (ILMDAS-551) ----


@pytest.mark.django_db
def test_admin_registers_librarian_who_sets_password_from_invite(api_client):
    admin = make_user("admin", ROLE_SYSTEM_ADMINISTRATOR)
    api_client.force_authenticate(admin)

    response = api_client.post(
        "/api/v1/users/staff/",
        {
            "username": "librarian1",
            "email": "librarian1@example.org",
            "first_name": "Lensa",
            "roles": [ROLE_LIBRARIAN],
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.data["status"] == UserAccountStatus.PENDING
    staff = User.objects.get(username="librarian1")
    assert not staff.has_usable_password()
    assert staff.is_active is False
    assert _roles(staff) == {ROLE_GUEST, ROLE_LIBRARIAN}
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["librarian1@example.org"]
    assert "/accept-invite?" in mail.outbox[0].body

    api_client.force_authenticate(None)
    accepted = api_client.post(
        "/api/v1/auth/invite/accept/",
        {**_link_params(mail.outbox[0]), "password": STRONG_PASSWORD},
        format="json",
    )
    assert accepted.status_code == 200

    staff.refresh_from_db()
    assert staff.status == UserAccountStatus.ACTIVE
    login = api_client.post(
        "/api/v1/auth/login/",
        {"username": "librarian1", "password": STRONG_PASSWORD},
        format="json",
    )
    assert login.status_code == 200
    assert ROLE_LIBRARIAN in {role["code"] for role in login.data["roles"]}
    assert _actions() == [
        "account.staff.created",
        "role.assigned",
        "account.invite.accepted",
        "auth.login",
    ]


@pytest.mark.django_db
def test_staff_registration_grants_every_requested_role_once(api_client):
    api_client.force_authenticate(make_user("admin", ROLE_SYSTEM_ADMINISTRATOR))
    response = api_client.post(
        "/api/v1/users/staff/",
        {
            "username": "manager1",
            "email": "manager1@example.org",
            "roles": [ROLE_MANAGER, ROLE_LIBRARIAN, ROLE_MANAGER],
        },
        format="json",
    )
    assert response.status_code == 201
    assert _roles(User.objects.get(username="manager1")) == {
        ROLE_GUEST,
        ROLE_MANAGER,
        ROLE_LIBRARIAN,
    }
    assert _actions().count("role.assigned") == 2


@pytest.mark.django_db
def test_non_administrator_cannot_register_staff(api_client):
    api_client.force_authenticate(make_user("lib", ROLE_LIBRARIAN))
    response = api_client.post(
        "/api/v1/users/staff/",
        {"username": "x", "email": "x@example.org", "roles": [ROLE_LIBRARIAN]},
        format="json",
    )
    assert response.status_code == 403
    assert not User.objects.filter(username="x").exists()


@pytest.mark.django_db
def test_anonymous_cannot_register_staff(api_client):
    response = api_client.post(
        "/api/v1/users/staff/",
        {"username": "x", "email": "x@example.org", "roles": [ROLE_LIBRARIAN]},
        format="json",
    )
    assert response.status_code in (401, 403)


@pytest.mark.django_db
@pytest.mark.parametrize("roles", [["member"], ["guest"], [], ["no_such_role"]])
def test_staff_registration_accepts_staff_roles_only(api_client, roles):
    api_client.force_authenticate(make_user("admin", ROLE_SYSTEM_ADMINISTRATOR))
    response = api_client.post(
        "/api/v1/users/staff/",
        {"username": "x", "email": "x@example.org", "roles": roles},
        format="json",
    )
    assert response.status_code == 400
    assert "roles" in response.data["errors"]


@pytest.mark.django_db
def test_staff_registration_rejects_taken_details_generically(api_client):
    make_user("taken", email="taken@example.org")
    api_client.force_authenticate(make_user("admin", ROLE_SYSTEM_ADMINISTRATOR))
    for details in (
        {"username": "TAKEN", "email": "new@example.org"},
        {"username": "new", "email": "Taken@Example.org"},
    ):
        response = api_client.post(
            "/api/v1/users/staff/", {**details, "roles": [ROLE_LIBRARIAN]}, format="json"
        )
        assert response.status_code == 400
        assert response.data["errors"] == {"non_field_errors": [DUPLICATE_ACCOUNT_MESSAGE]}


@pytest.mark.django_db
def test_invite_link_is_single_use(api_client):
    api_client.force_authenticate(make_user("admin", ROLE_SYSTEM_ADMINISTRATOR))
    api_client.post(
        "/api/v1/users/staff/",
        {"username": "lib2", "email": "lib2@example.org", "roles": [ROLE_LIBRARIAN]},
        format="json",
    )
    params = _link_params(mail.outbox[0])
    api_client.force_authenticate(None)
    first = api_client.post(
        "/api/v1/auth/invite/accept/", {**params, "password": STRONG_PASSWORD}, format="json"
    )
    again = api_client.post(
        "/api/v1/auth/invite/accept/",
        {**params, "password": OTHER_STRONG_PASSWORD},
        format="json",
    )
    assert first.status_code == 200
    assert again.status_code == 400
    assert again.data["errors"] == {"token": ["This link is invalid or has expired."]}


@pytest.mark.django_db
def test_expired_invite_link_is_rejected(api_client, monkeypatch, settings):
    api_client.force_authenticate(make_user("admin", ROLE_SYSTEM_ADMINISTRATOR))
    api_client.post(
        "/api/v1/users/staff/",
        {"username": "lib3", "email": "lib3@example.org", "roles": [ROLE_LIBRARIAN]},
        format="json",
    )
    params = _link_params(mail.outbox[0])
    issued = staff_invite_tokens._now()
    monkeypatch.setattr(
        staff_invite_tokens,
        "_now",
        lambda: issued.replace(year=issued.year + 1),
    )
    api_client.force_authenticate(None)
    response = api_client.post(
        "/api/v1/auth/invite/accept/", {**params, "password": STRONG_PASSWORD}, format="json"
    )
    assert response.status_code == 400
    assert User.objects.get(username="lib3").status == UserAccountStatus.PENDING


@pytest.mark.django_db
def test_invite_rejects_weak_password(api_client):
    api_client.force_authenticate(make_user("admin", ROLE_SYSTEM_ADMINISTRATOR))
    api_client.post(
        "/api/v1/users/staff/",
        {"username": "lib4", "email": "lib4@example.org", "roles": [ROLE_LIBRARIAN]},
        format="json",
    )
    api_client.force_authenticate(None)
    response = api_client.post(
        "/api/v1/auth/invite/accept/",
        {**_link_params(mail.outbox[0]), "password": WEAK_PASSWORD},
        format="json",
    )
    assert response.status_code == 400
    assert "password" in response.data["errors"]
    assert User.objects.get(username="lib4").status == UserAccountStatus.PENDING


@pytest.mark.django_db
def test_invite_link_cannot_verify_an_email(api_client):
    """The two link types are signed differently, so one can't stand in for the other."""
    api_client.force_authenticate(make_user("admin", ROLE_SYSTEM_ADMINISTRATOR))
    api_client.post(
        "/api/v1/users/staff/",
        {"username": "lib5", "email": "lib5@example.org", "roles": [ROLE_LIBRARIAN]},
        format="json",
    )
    api_client.force_authenticate(None)
    response = api_client.post(
        "/api/v1/auth/verify-email/", _link_params(mail.outbox[0]), format="json"
    )
    assert response.status_code == 400
    assert User.objects.get(username="lib5").status == UserAccountStatus.PENDING


# ---- Self-registration (ILMDAS-552) ----


@pytest.mark.django_db
def test_self_registration_creates_pending_account_that_cannot_sign_in(api_client):
    make_user("seed")  # seeds the roles
    response = api_client.post("/api/v1/auth/register/", _registration(), format="json")

    assert response.status_code == 201
    assert response.data["status"] == UserAccountStatus.PENDING
    user = User.objects.get(username="chaltu")
    assert user.status == UserAccountStatus.PENDING
    assert _roles(user) == {ROLE_GUEST}
    assert len(mail.outbox) == 1
    assert "/verify-email?" in mail.outbox[0].body

    login = api_client.post(
        "/api/v1/auth/login/",
        {"username": "chaltu", "password": STRONG_PASSWORD},
        format="json",
    )
    assert login.status_code == 401


@pytest.mark.django_db
def test_verified_account_is_an_active_guest(api_client):
    make_user("seed")
    api_client.post("/api/v1/auth/register/", _registration(), format="json")
    verified = api_client.post(
        "/api/v1/auth/verify-email/", _link_params(mail.outbox[0]), format="json"
    )
    assert verified.status_code == 200

    user = User.objects.get(username="chaltu")
    assert user.status == UserAccountStatus.ACTIVE
    assert user.is_guest is True
    assert user.is_member is False
    login = api_client.post(
        "/api/v1/auth/login/",
        {"username": "chaltu", "password": STRONG_PASSWORD},
        format="json",
    )
    assert login.status_code == 200
    assert [role["code"] for role in login.data["roles"]] == [ROLE_GUEST]
    assert _actions() == ["account.registered", "account.email_verified", "auth.login"]


@pytest.mark.django_db
def test_verification_link_is_single_use(api_client):
    make_user("seed")
    api_client.post("/api/v1/auth/register/", _registration(), format="json")
    params = _link_params(mail.outbox[0])
    assert api_client.post("/api/v1/auth/verify-email/", params, format="json").status_code == 200
    assert api_client.post("/api/v1/auth/verify-email/", params, format="json").status_code == 400


@pytest.mark.django_db
def test_expired_verification_link_is_rejected_and_a_new_one_can_be_requested(
    api_client, monkeypatch
):
    make_user("seed")
    api_client.post("/api/v1/auth/register/", _registration(), format="json")
    old_params = _link_params(mail.outbox[0])

    issued = email_verification_tokens._now()
    later = issued.replace(year=issued.year + 1)
    monkeypatch.setattr(email_verification_tokens, "_now", lambda: later)
    expired = api_client.post("/api/v1/auth/verify-email/", old_params, format="json")
    assert expired.status_code == 400

    resend = api_client.post(
        "/api/v1/auth/verify-email/resend/", {"email": "CHALTU@example.org"}, format="json"
    )
    assert resend.status_code == 200
    assert len(mail.outbox) == 2
    fresh = api_client.post(
        "/api/v1/auth/verify-email/", _link_params(mail.outbox[1]), format="json"
    )
    assert fresh.status_code == 200
    assert User.objects.get(username="chaltu").status == UserAccountStatus.ACTIVE


@pytest.mark.django_db
def test_resend_gives_the_same_answer_for_unknown_and_active_emails(api_client):
    make_user("active", email="active@example.org")
    unknown = api_client.post(
        "/api/v1/auth/verify-email/resend/", {"email": "nobody@example.org"}, format="json"
    )
    active = api_client.post(
        "/api/v1/auth/verify-email/resend/", {"email": "active@example.org"}, format="json"
    )
    assert unknown.status_code == active.status_code == 200
    assert unknown.data == active.data
    assert mail.outbox == []


@pytest.mark.django_db
def test_resend_does_not_email_pending_staff_invites(api_client):
    api_client.force_authenticate(make_user("admin", ROLE_SYSTEM_ADMINISTRATOR))
    api_client.post(
        "/api/v1/users/staff/",
        {"username": "lib6", "email": "lib6@example.org", "roles": [ROLE_LIBRARIAN]},
        format="json",
    )
    api_client.force_authenticate(None)
    api_client.post(
        "/api/v1/auth/verify-email/resend/", {"email": "lib6@example.org"}, format="json"
    )
    assert len(mail.outbox) == 1  # only the original invite


@pytest.mark.django_db
@pytest.mark.parametrize(
    "overrides",
    [
        {"username": "Existing"},
        {"email": "EXISTING@example.org"},
    ],
)
def test_duplicate_username_or_email_gets_one_generic_error(api_client, overrides):
    make_user("existing", email="existing@example.org")
    response = api_client.post("/api/v1/auth/register/", _registration(**overrides), format="json")
    assert response.status_code == 400
    assert response.data["errors"] == {"non_field_errors": [DUPLICATE_ACCOUNT_MESSAGE]}


@pytest.mark.django_db
def test_registration_requires_accepting_the_terms(api_client):
    response = api_client.post(
        "/api/v1/auth/register/", _registration(accept_terms=False), format="json"
    )
    assert response.status_code == 400
    assert "accept_terms" in response.data["errors"]


@pytest.mark.django_db
@pytest.mark.parametrize("password", ["short1!", "123456789012345", "chaltu@example.org"])
def test_registration_enforces_the_password_policy(api_client, password):
    response = api_client.post(
        "/api/v1/auth/register/", _registration(password=password), format="json"
    )
    assert response.status_code == 400
    assert "password" in response.data["errors"]
    assert not User.objects.filter(username="chaltu").exists()


@pytest.mark.django_db
def test_repeated_signups_are_throttled(api_client, monkeypatch):
    monkeypatch.setattr(RegistrationRateThrottle, "rate", "2/hour", raising=False)
    for number in range(2):
        response = api_client.post(
            "/api/v1/auth/register/",
            _registration(username=f"user{number}", email=f"user{number}@example.org"),
            format="json",
        )
        assert response.status_code == 201
    blocked = api_client.post(
        "/api/v1/auth/register/",
        _registration(username="user9", email="user9@example.org"),
        format="json",
    )
    assert blocked.status_code == 429
    assert not User.objects.filter(username="user9").exists()


@pytest.mark.django_db
def test_registration_requires_csrf(client_with_csrf_checks):
    response = client_with_csrf_checks.post(
        "/api/v1/auth/register/", _registration(), format="json"
    )
    assert response.status_code == 403
    assert not User.objects.filter(username="chaltu").exists()


@pytest.fixture
def client_with_csrf_checks():
    from rest_framework.test import APIClient

    return APIClient(enforce_csrf_checks=True)
