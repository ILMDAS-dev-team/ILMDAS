"""Tests for audit trail records and sensitive event recording."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model

from apps.audit.models import AuditRecord, record_audit_event

TEST_PASSWORD = "Test@123456!"  # pragma: allowlist secret
TEST_SECRET_TOKEN = "secret_token_123"  # pragma: allowlist secret


def test_audit_package_imports():
    import apps.audit as app

    assert app.__name__ == "apps.audit"


@pytest.mark.django_db
def test_audit_record_creation_and_fields():
    user_model = get_user_model()
    actor = user_model.objects.create_user(username="auditor", password=TEST_PASSWORD)

    record = record_audit_event(
        action="test.action",
        actor=actor,
        object_type="TestObject",
        object_id="123",
        details={"key": "value"},
    )

    assert record.id is not None
    assert record.actor == actor
    assert record.actor_username == "auditor"
    assert record.action == "test.action"
    assert record.object_type == "TestObject"
    assert record.object_id == "123"
    assert record.details == {"key": "value"}
    assert record.timestamp is not None
    assert "auditor" in str(record)
    assert "test.action" in str(record)
    assert AuditRecord.objects.count() == 1


@pytest.mark.django_db
def test_audit_record_sanitizes_passwords_and_secrets():
    record = record_audit_event(
        action="auth.password_change",
        actor="admin",
        object_type="user",
        object_id="1",
        details={
            "username": "librarian_01",
            "password": TEST_PASSWORD,
            "apiKey": "key-123",
            "api-key": "key-456",
            "privateKey": "priv-789",
            "authorization": "Bearer xyz",
            "cookie": "sessionid=abc",
            "sessionid": "abc",
            "otp": "123456",
            "nested": {"token": TEST_SECRET_TOKEN, "normal": "ok"},
        },
    )
    assert record.details["password"] == "[REDACTED]"
    assert record.details["apiKey"] == "[REDACTED]"
    assert record.details["api-key"] == "[REDACTED]"
    assert record.details["privateKey"] == "[REDACTED]"
    assert record.details["authorization"] == "[REDACTED]"
    assert record.details["cookie"] == "[REDACTED]"
    assert record.details["sessionid"] == "[REDACTED]"
    assert record.details["otp"] == "[REDACTED]"
    assert record.details["nested"]["token"] == "[REDACTED]"
    assert record.details["nested"]["normal"] == "ok"
    assert TEST_PASSWORD not in str(record.details)
