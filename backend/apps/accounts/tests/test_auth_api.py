"""API tests for login, logout, and session (SEC-01 / ILMDAS-27)."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.accounts.models import UserAccountStatus, UserRole

UserAccount = get_user_model()
TEST_PASSWORD = "correct-horse-pass"  # pragma: allowlist secret


@pytest.fixture
def active_user(db):
    return UserAccount.objects.create_user(username="active", password=TEST_PASSWORD)


@pytest.fixture
def inactive_user(db):
    return UserAccount.objects.create_user(
        username="inactive",
        password=TEST_PASSWORD,
        status=UserAccountStatus.INACTIVE,
    )


@pytest.mark.django_db
def test_login_success_creates_session_and_updates_last_login(api_client, active_user):
    assert active_user.last_login is None
    response = api_client.post(
        "/api/v1/auth/login/",
        {"username": "active", "password": TEST_PASSWORD},
        format="json",
    )
    assert response.status_code == 200
    assert response.data["authenticated"] is True
    assert response.data["username"] == "active"
    assert response.data["status"] == UserAccountStatus.ACTIVE
    active_user.refresh_from_db()
    assert active_user.last_login is not None

    me = api_client.get("/api/v1/auth/me/")
    assert me.status_code == 200
    assert me.data["authenticated"] is True


@pytest.mark.django_db
def test_login_wrong_password_returns_generic_authentication_error(api_client, active_user):
    response = api_client.post(
        "/api/v1/auth/login/",
        {"username": "active", "password": "wrong-secret-val"},  # pragma: allowlist secret
        format="json",
    )
    assert response.status_code == 401
    assert response.data["code"] == "authentication_error"
    assert "password" not in response.data["message"].lower()
    assert "active" not in response.data["message"].lower()


@pytest.mark.django_db
def test_login_unknown_user_returns_same_generic_error(api_client):
    response = api_client.post(
        "/api/v1/auth/login/",
        {"username": "missing", "password": TEST_PASSWORD},
        format="json",
    )
    assert response.status_code == 401
    assert response.data["code"] == "authentication_error"


@pytest.mark.django_db
def test_login_inactive_account_returns_same_generic_error(api_client, inactive_user):
    response = api_client.post(
        "/api/v1/auth/login/",
        {"username": "inactive", "password": TEST_PASSWORD},
        format="json",
    )
    assert response.status_code == 401
    assert response.data["code"] == "authentication_error"


@pytest.mark.django_db
def test_logout_invalidates_session(api_client, active_user):
    api_client.post(
        "/api/v1/auth/login/",
        {"username": "active", "password": TEST_PASSWORD},
        format="json",
    )
    assert api_client.get("/api/v1/auth/me/").status_code == 200

    logout = api_client.post("/api/v1/auth/logout/", {}, format="json")
    assert logout.status_code == 200
    assert logout.data["authenticated"] is False

    me = api_client.get("/api/v1/auth/me/")
    assert me.status_code == 401
    assert me.data["code"] == "authentication_error"


@pytest.mark.django_db
def test_csrf_endpoint_sets_cookie(api_client):
    response = api_client.get("/api/v1/auth/csrf/")
    assert response.status_code == 200
    assert "csrfToken" in response.data
    assert "csrftoken" in response.cookies


@pytest.mark.django_db
def test_login_failure_uses_safe_invalid_credentials_message(api_client, active_user):
    response = api_client.post(
        "/api/v1/auth/login/",
        {"username": "active", "password": "wrong-secret-val"},  # pragma: allowlist secret
        format="json",
    )
    assert response.status_code == 401
    assert response.data["code"] == "authentication_error"
    assert response.data["message"] == "Sign-in failed. Check your details and try again."


@pytest.mark.django_db
def test_login_without_csrf_token_is_rejected(active_user):
    client = APIClient(enforce_csrf_checks=True)
    response = client.post(
        "/api/v1/auth/login/",
        {"username": "active", "password": TEST_PASSWORD},
        format="json",
    )
    assert response.status_code == 403
    assert response.data["code"] == "authorization_error"
    assert "sessionid" not in response.cookies


@pytest.mark.django_db
def test_login_with_csrf_token_from_csrf_endpoint_succeeds(active_user):
    client = APIClient(enforce_csrf_checks=True)
    token = client.get("/api/v1/auth/csrf/").data["csrfToken"]
    response = client.post(
        "/api/v1/auth/login/",
        {"username": "active", "password": TEST_PASSWORD},
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )
    assert response.status_code == 200
    assert response.data["authenticated"] is True


@pytest.mark.django_db
def test_login_from_allowed_frontend_origin_gets_credentialed_cors(active_user):
    client = APIClient(enforce_csrf_checks=True)
    token = client.get("/api/v1/auth/csrf/").data["csrfToken"]
    response = client.post(
        "/api/v1/auth/login/",
        {"username": "active", "password": TEST_PASSWORD},
        format="json",
        HTTP_X_CSRFTOKEN=token,
        HTTP_ORIGIN="http://localhost:3010",
    )
    assert response.status_code == 200
    assert response["Access-Control-Allow-Origin"] == "http://localhost:3010"
    assert response["Access-Control-Allow-Credentials"] == "true"


def test_cors_preflight_allows_frontend_headers(client):
    response = client.options(
        "/api/v1/auth/login/",
        HTTP_ORIGIN="http://localhost:3010",
        HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
        HTTP_ACCESS_CONTROL_REQUEST_HEADERS="content-type,x-csrftoken,x-correlation-id",
    )
    allowed = response["Access-Control-Allow-Headers"].lower()
    for header in ("content-type", "x-csrftoken", "x-correlation-id"):
        assert header in allowed


def test_admin_can_edit_role_and_personal_fields():
    from django.contrib import admin

    model_admin = admin.site._registry[UserAccount]
    edit_fields = {f for _, opts in model_admin.fieldsets for f in opts["fields"]}
    add_fields = {f for _, opts in model_admin.add_fieldsets for f in opts["fields"]}
    for field in ("email", "first_name", "last_name"):
        assert field in edit_fields
        assert field in add_fields
    # Roles are assigned through the UserRole inline, not a field on the user.
    assert any(inline.model is UserRole for inline in model_admin.inlines)
