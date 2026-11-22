"""Tests for audit trail records and sensitive event recording."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model

from apps.audit.models import AuditRecord, record_audit_event


def test_audit_package_imports():
    import apps.audit as app

    assert app.__name__ == "apps.audit"


@pytest.mark.django_db
def test_audit_record_creation_and_fields():
    user_model = get_user_model()
    actor = user_model.objects.create_user(username="auditor", password="ValidPassword123!")

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
