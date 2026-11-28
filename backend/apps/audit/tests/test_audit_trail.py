"""ILMDAS-31: append-only audit trail and read-only review API (test refs SEC-03, SEC-05)."""

from __future__ import annotations

import pytest
from django.contrib import admin
from django.db import connection
from django.test import RequestFactory
from rest_framework.test import APIClient

from apps.accounts.constants import (
    ROLE_LIBRARIAN,
    ROLE_SYSTEM_ADMINISTRATOR,
)
from apps.accounts.models import Role, User, UserRole
from apps.accounts.testing import DEFAULT_TEST_PASSWORD, make_user
from apps.audit.models import (
    AuditOutcome,
    AuditRecord,
    AuditRecordImmutable,
    record_audit_event,
)

WRONG_PASSWORD = "Wrong@Pass000!"  # pragma: allowlist secret
EVENTS_URL = "/api/v1/audit/events/"


def _client(user: User | None = None, correlation_id: str = "") -> APIClient:
    client = APIClient(HTTP_X_CORRELATION_ID=correlation_id) if correlation_id else APIClient()
    if user is not None:
        client.force_authenticate(user)
    return client


def _only(action: str) -> AuditRecord:
    events = list(AuditRecord.objects.filter(action=action))
    assert len(events) == 1, f"expected exactly one {action} event, got {len(events)}"
    return events[0]


# ---- Events are written (ILMDAS-297) ----


@pytest.mark.django_db
def test_login_success_creates_one_event_with_correlation_id():
    make_user("alice")
    response = _client(correlation_id="cid-login-ok").post(
        "/api/v1/auth/login/",
        {"username": "alice", "password": DEFAULT_TEST_PASSWORD},
        format="json",
    )
    assert response.status_code == 200
    event = _only("auth.login")
    assert event.outcome == AuditOutcome.SUCCESS
    assert event.correlation_id == "cid-login-ok"
    assert event.actor_username == "alice"


@pytest.mark.django_db
def test_login_failure_creates_one_failure_event_with_correlation_id():
    make_user("bob")
    response = _client(correlation_id="cid-login-bad").post(
        "/api/v1/auth/login/",
        {"username": "bob", "password": WRONG_PASSWORD},
        format="json",
    )
    assert response.status_code == 401
    event = _only("auth.login.failed")
    assert event.outcome == AuditOutcome.FAILURE
    assert event.correlation_id == "cid-login-bad"
    assert WRONG_PASSWORD not in str(event.details)


@pytest.mark.django_db
def test_role_assign_and_remove_via_api_each_create_one_event():
    admin_user = make_user("api_admin", ROLE_SYSTEM_ADMINISTRATOR)
    target = make_user("api_target")
    client = _client(admin_user, correlation_id="cid-role")

    assigned = client.post(
        f"/api/v1/users/{target.id}/roles/", {"role_code": ROLE_LIBRARIAN}, format="json"
    )
    assert assigned.status_code == 201
    removed = client.delete(f"/api/v1/users/{target.id}/roles/{ROLE_LIBRARIAN}/")
    assert removed.status_code == 200

    for action in ("role.assigned", "role.revoked"):
        event = _only(action)
        assert event.correlation_id == "cid-role"
        assert event.outcome == AuditOutcome.SUCCESS
        assert event.details["role_code"] == ROLE_LIBRARIAN


def _admin_role_formset(request, user, data):
    model_admin = admin.site._registry[User]
    inline = model_admin.get_inline_instances(request, user)[0]
    formset_class = inline.get_formset(request, user)
    prefix = formset_class.get_default_prefix()
    full = {f"{prefix}-{key}": value for key, value in data.items()}
    full.update({f"{prefix}-MIN_NUM_FORMS": "0", f"{prefix}-MAX_NUM_FORMS": "1000"})
    formset = formset_class(full, instance=user, prefix=prefix)
    assert formset.is_valid(), formset.errors
    return model_admin, formset


@pytest.mark.django_db
def test_role_changes_in_django_admin_are_audited():
    superuser = User.objects.create_superuser(
        username="root", password=DEFAULT_TEST_PASSWORD, email="root@example.org"
    )
    target = make_user("admin_target")
    librarian = Role.objects.get(code=ROLE_LIBRARIAN)
    request = RequestFactory().post("/admin/", HTTP_X_CORRELATION_ID="cid-admin")
    request.user = superuser
    request.correlation_id = "cid-admin"

    # Add a role
    existing = list(target.user_roles.all())
    data = {"TOTAL_FORMS": str(len(existing) + 1), "INITIAL_FORMS": str(len(existing))}
    for i, assignment in enumerate(existing):
        data |= {
            f"{i}-id": str(assignment.id),
            f"{i}-user": str(target.id),
            f"{i}-role": str(assignment.role_id),
        }
    data |= {f"{len(existing)}-role": str(librarian.id), f"{len(existing)}-user": str(target.id)}
    model_admin, formset = _admin_role_formset(request, target, data)
    model_admin.save_formset(request, None, formset, True)

    added = UserRole.objects.get(user=target, role=librarian)
    assert added.assigned_by == superuser
    assert _only("role.assigned").details["via"] == "admin"

    # Remove it again
    rows = list(target.user_roles.order_by("id"))
    data = {"TOTAL_FORMS": str(len(rows)), "INITIAL_FORMS": str(len(rows))}
    for i, assignment in enumerate(rows):
        data |= {
            f"{i}-id": str(assignment.id),
            f"{i}-user": str(target.id),
            f"{i}-role": str(assignment.role_id),
        }
        if assignment.role_id == librarian.id:
            data[f"{i}-DELETE"] = "on"
    model_admin, formset = _admin_role_formset(request, target, data)
    model_admin.save_formset(request, None, formset, True)

    assert not UserRole.objects.filter(user=target, role=librarian).exists()
    revoked = _only("role.revoked")
    assert revoked.correlation_id == "cid-admin"
    assert revoked.actor == superuser


# ---- Append-only (ILMDAS-296 / ILMDAS-299) ----


@pytest.mark.django_db
def test_audit_records_cannot_be_updated_or_deleted_through_the_orm():
    event = record_audit_event(action="test.event", actor="system")

    event.action = "tampered"
    with pytest.raises(AuditRecordImmutable):
        event.save()
    with pytest.raises(AuditRecordImmutable):
        event.delete()
    with pytest.raises(AuditRecordImmutable):
        AuditRecord.objects.filter(pk=event.pk).update(action="tampered")
    with pytest.raises(AuditRecordImmutable):
        AuditRecord.objects.filter(pk=event.pk).delete()

    assert AuditRecord.objects.get(pk=event.pk).action == "test.event"


@pytest.mark.django_db
def test_user_with_audit_history_cannot_be_deleted():
    from django.db.models import ProtectedError

    user = make_user("historic")
    record_audit_event(action="test.event", actor=user)
    with pytest.raises(ProtectedError):
        user.delete()


@pytest.mark.django_db
@pytest.mark.skipif(
    connection.vendor != "postgresql", reason="database trigger is installed on PostgreSQL only"
)
def test_database_refuses_update_and_delete_on_postgresql():
    from django.db import DatabaseError, transaction

    event = record_audit_event(action="test.event", actor="system")
    table = connection.ops.quote_name(AuditRecord._meta.db_table)
    for sql in (
        f"UPDATE {table} SET action = 'tampered' WHERE id = %s",  # noqa: S608
        f"DELETE FROM {table} WHERE id = %s",  # noqa: S608
    ):
        with pytest.raises(DatabaseError), transaction.atomic(), connection.cursor() as cursor:
            cursor.execute(sql, [event.pk])


# ---- Read-only review API (ILMDAS-298 / ILMDAS-299) ----


@pytest.mark.django_db
def test_librarian_cannot_read_update_or_delete_audit_events():
    event = record_audit_event(action="test.event", actor="system")
    client = _client(make_user("lib", ROLE_LIBRARIAN))
    detail = f"{EVENTS_URL}{event.pk}/"

    assert client.get(EVENTS_URL).status_code == 403
    assert client.get(detail).status_code == 403
    assert client.patch(detail, {"action": "x"}, format="json").status_code == 403
    assert client.put(detail, {"action": "x"}, format="json").status_code == 403
    assert client.delete(detail).status_code == 403
    assert AuditRecord.objects.get(pk=event.pk).action == "test.event"


@pytest.mark.django_db
def test_admin_has_no_write_methods_on_audit_events():
    event = record_audit_event(action="test.event", actor="system")
    client = _client(make_user("reviewer", ROLE_SYSTEM_ADMINISTRATOR))
    detail = f"{EVENTS_URL}{event.pk}/"

    assert client.get(detail).status_code == 200
    assert client.post(EVENTS_URL, {"action": "x"}, format="json").status_code == 405
    assert client.patch(detail, {"action": "x"}, format="json").status_code == 405
    assert client.put(detail, {"action": "x"}, format="json").status_code == 405
    assert client.delete(detail).status_code == 405
    assert AuditRecord.objects.filter(pk=event.pk).exists()


@pytest.mark.django_db
def test_anonymous_request_is_rejected():
    assert APIClient().get(EVENTS_URL).status_code == 401


@pytest.mark.django_db
def test_admin_can_filter_by_actor_action_and_date():
    reviewer = make_user("reviewer2", ROLE_SYSTEM_ADMINISTRATOR)
    record_audit_event(action="auth.login", actor="carol")
    record_audit_event(action="auth.login.failed", actor="dave", outcome=AuditOutcome.FAILURE)
    record_audit_event(action="role.assigned", actor="carol")
    client = _client(reviewer)

    def actions(query: str) -> list[str]:
        response = client.get(f"{EVENTS_URL}?{query}")
        assert response.status_code == 200
        return sorted(row["action"] for row in response.data["results"])

    assert actions("actor=carol") == ["auth.login", "role.assigned"]
    assert actions("action=auth.login") == ["auth.login"]
    assert actions("action=auth.") == ["auth.login", "auth.login.failed"]
    assert actions("date_from=2000-01-01&date_to=2999-12-31&actor=dave") == ["auth.login.failed"]
    assert actions("date_to=2000-01-01") == []
    assert client.get(f"{EVENTS_URL}?date_from=not-a-date").status_code == 400


@pytest.mark.django_db
def test_review_api_never_returns_submitted_secrets():
    reviewer = make_user("reviewer3", ROLE_SYSTEM_ADMINISTRATOR)
    record_audit_event(
        action="test.secret",
        actor="system",
        details={"password": WRONG_PASSWORD, "note": "ok"},
    )
    body = _client(reviewer).get(f"{EVENTS_URL}?action=test.secret").content.decode()
    assert WRONG_PASSWORD not in body
    assert "[REDACTED]" in body
