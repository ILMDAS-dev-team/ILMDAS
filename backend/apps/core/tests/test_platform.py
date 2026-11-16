"""Scaffold tests for settings, stores, IIIF, and the API error contract."""

from __future__ import annotations

import base64
import hashlib
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import dj_database_url
import pytest
from config.settings.env import require_env
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from rest_framework.exceptions import NotAuthenticated, PermissionDenied, Throttled, ValidationError

from apps.core.exceptions import Conflict, api_exception_handler
from apps.core.iiif import IiifClient
from apps.core.models import ObjectReference
from apps.core.search import CatalogueIndex
from apps.core.storage import ObjectStorage, StoredObject

BACKEND_DIR = Path(__file__).resolve().parents[3]
REPO_DIR = BACKEND_DIR.parent
APP_NAMES = [
    "core",
    "accounts",
    "catalogue",
    "circulation",
    "archive",
    "publishing",
    "payments",
    "audit",
]


def test_required_environment_fails_closed(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(ImproperlyConfigured, match="SECRET_KEY"):
        require_env("SECRET_KEY")


def test_development_settings_refuse_to_start_without_required_variables():
    env = os.environ.copy()
    env["ILMDAS_SKIP_ENV_FILE"] = "1"
    env.pop("SECRET_KEY", None)
    env.pop("DATABASE_URL", None)
    result = subprocess.run(
        [sys.executable, "-c", "import config.settings.development"],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "SECRET_KEY" in result.stderr + result.stdout


def test_each_app_has_models_migrations_and_tests():
    for name in APP_NAMES:
        app_dir = BACKEND_DIR / "apps" / name
        assert (app_dir / "models.py").is_file()
        assert (app_dir / "migrations").is_dir()
        assert (app_dir / "tests").is_dir()


def test_example_env_file_contains_names_only():
    text = (BACKEND_DIR / ".env.example").read_text(encoding="utf-8")
    assert "SECRET_KEY=" in text
    assert "DATABASE_URL=" in text
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        _name, value = stripped.split("=", 1)
        assert value.strip() == ""
    assert "AKIA" not in text


def test_postgres_url_selects_the_postgres_engine():
    config = dj_database_url.parse("postgres://USER:PASSWORD@localhost:5432/ilmdas")
    assert config["ENGINE"] == "django.db.backends.postgresql"


@pytest.mark.django_db
def test_migrations_apply():
    call_command("migrate", verbosity=0, interactive=False)
    record = ObjectReference.objects.create(
        object_key="manuscripts/fixture",
        reference="s3://ilmdas-digital-objects/manuscripts/fixture",
        checksum_sha256="abc",
    )
    assert record.id


def test_catalogue_index_can_be_created_and_deleted_outside_production():
    class Indices:
        def __init__(self):
            self.names: set[str] = set()

        def exists(self, index):
            return index in self.names

        def create(self, index, **_kwargs):
            self.names.add(index)

        def delete(self, index):
            self.names.remove(index)

    class Client:
        def __init__(self):
            self.indices = Indices()

        def ping(self):
            return True

    index = CatalogueIndex(client=Client(), index_name="ilmdas-catalogue")
    index.rebuild()
    assert index.client.indices.exists(index="ilmdas-catalogue")
    index.delete()
    assert not index.client.indices.exists(index="ilmdas-catalogue")


def test_private_upload_stores_a_reference_and_checksum():
    calls = {}

    class FakeClient:
        def put_object(self, **kwargs):
            calls.update(kwargs)

    storage = ObjectStorage(client=FakeClient(), bucket="ilmdas-digital-objects")
    stored = storage.put_private("manuscripts/1", b"page")
    assert calls["ACL"] == "private"
    assert stored.checksum_sha256 == hashlib.sha256(b"page").hexdigest()
    assert stored.reference == "s3://ilmdas-digital-objects/manuscripts/1"
    assert "http://" not in stored.reference
    assert "https://" not in stored.reference


@pytest.mark.django_db
def test_object_upload_is_not_anonymously_readable(api_client, django_user_model):
    user = django_user_model.objects.create_user(username="staff", password="local-only")
    body = b"page"
    stored = StoredObject(
        reference="s3://ilmdas-digital-objects/manuscripts/1",
        checksum_sha256=hashlib.sha256(body).hexdigest(),
        object_key="manuscripts/1",
    )
    api_client.force_authenticate(user)
    with patch("apps.core.views.ObjectStorage.put_private", return_value=stored):
        created = api_client.post(
            "/api/v1/storage/objects/",
            {"objectKey": "manuscripts/1", "bodyBase64": base64.b64encode(body).decode()},
            format="json",
        )
    assert created.status_code == 201
    assert created.data["checksumSha256"] == stored.checksum_sha256
    api_client.force_authenticate(None)
    denied = api_client.get(f"/api/v1/storage/objects/{created.data['id']}/")
    assert denied.status_code == 401
    assert denied.data["code"] == "authentication_error"


@pytest.mark.parametrize(
    ("target", "check"),
    [
        ("apps.core.views.database_health", "database"),
        ("apps.core.views.CatalogueIndex.health", "elasticsearch"),
        ("apps.core.views.ObjectStorage.health", "objectStorage"),
    ],
)
def test_health_fails_when_a_store_is_unreachable(api_client, target, check):
    with patch(target, return_value={"ok": False, "detail": "unreachable"}):
        response = api_client.get("/api/v1/health/")
    assert response.status_code == 503
    assert response.data["status"] == "failed"
    assert response.data["checks"][check] == {"ok": False, "detail": "unreachable"}


def test_iiif_fixture_and_missing_endpoint():
    missing = IiifClient(endpoint="")
    assert missing.configuration_status()["status"] == "not_configured"
    assert missing.image_info("fixture-image")["status"] == "not_configured"

    seen = {}

    def fake_get(url):
        seen["url"] = url
        return {"@id": url, "width": 10, "height": 10}

    configured = IiifClient(endpoint="http://iiif.internal/iiif/2", http_get=fake_get)
    info = configured.image_info("fixture-image")
    assert info["status"] == "ok"
    assert seen["url"] == "http://iiif.internal/iiif/2/fixture-image/info.json"
    assert "/public/" not in seen["url"]


def test_public_routes_do_not_serve_iiif_images():
    from django.urls import get_resolver

    patterns = " ".join(str(pattern.pattern) for pattern in get_resolver().url_patterns)
    assert "info.json" not in patterns
    assert "iiif" not in patterns


@pytest.mark.django_db
def test_validation_and_authentication_errors_use_different_codes(api_client):
    validation = api_client.post("/api/v1/contract/validation/", {}, format="json")
    authentication = api_client.get("/api/v1/contract/session/")
    assert validation.status_code == 400
    assert authentication.status_code == 401
    assert validation.data["code"] == "validation_error"
    assert authentication.data["code"] == "authentication_error"
    assert validation.data["code"] != authentication.data["code"]
    for response in (validation, authentication):
        assert response.data["correlationId"]
        rendered = str(response.data)
        assert "Traceback" not in rendered
        assert "SECRET" not in rendered
        assert response.headers["X-Correlation-ID"] == response.data["correlationId"]


def test_documented_error_codes_include_correlation_and_hide_internals():
    request = type("Request", (), {"correlation_id": "cid-123"})()
    cases = [
        (ValidationError({"name": ["This field is required."]}), "validation_error", 400),
        (NotAuthenticated(), "authentication_error", 401),
        (PermissionDenied(), "authorization_error", 403),
        (Conflict(), "conflict", 409),
        (Throttled(wait=1), "rate_limit", 429),
        (RuntimeError("database password=super-secret"), "unavailable", 503),
    ]
    for exc, code, status in cases:
        response = api_exception_handler(exc, {"request": request})
        assert response.status_code == status
        assert response.data["code"] == code
        assert response.data["correlationId"] == "cid-123"
        assert "super-secret" not in str(response.data)
        assert "Traceback" not in str(response.data)


def test_ci_workflow_runs_both_test_suites_and_fails_on_failure():
    workflow = (REPO_DIR / ".github" / "workflows" / "ci-cd.yml").read_text(encoding="utf-8")
    assert "pytest" in workflow
    assert "npm test" in workflow
    assert "continue-on-error: true" not in workflow
