"""API tests for login, logout, and session (SEC-01 / ILMDAS-27)."""

import pytest
from django.contrib.auth import get_user_model

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
        status=UserAccount.Status.INACTIVE,
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
    assert response.data["status"] == UserAccount.Status.ACTIVE
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
