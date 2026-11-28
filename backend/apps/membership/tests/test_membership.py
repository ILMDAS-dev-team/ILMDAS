"""Membership plans (ILMDAS-553) and the request, payment and approval flow (ILMDAS-554)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from io import StringIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.views import APIView

from apps.accounts.constants import (
    ROLE_GUEST,
    ROLE_JOURNAL_EDITOR,
    ROLE_LIBRARIAN,
    ROLE_MANAGER,
    ROLE_MEMBER,
    ROLE_SYSTEM_ADMINISTRATOR,
)
from apps.accounts.testing import make_user
from apps.audit.models import AuditRecord
from apps.core.storage import ObjectStorageError, StoredObject
from apps.membership import services
from apps.membership.models import (
    MembershipPlan,
    MembershipRequest,
    MembershipSubscription,
)
from apps.membership.permissions import IsMember

PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF"
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16


class FakeStorage:
    """Stands in for ObjectStorage so tests don't need S3."""

    stored: list[str] = []
    fail = False

    def put_private(self, object_key, body, content_type="application/octet-stream"):
        if FakeStorage.fail:
            raise ObjectStorageError("storage is down")
        FakeStorage.stored.append(object_key)
        return StoredObject(
            reference=f"s3://test/{object_key}", checksum_sha256="0" * 64, object_key=object_key
        )


@pytest.fixture(autouse=True)
def fake_storage(monkeypatch):
    FakeStorage.stored = []
    FakeStorage.fail = False
    monkeypatch.setattr(services, "ObjectStorage", FakeStorage)
    return FakeStorage


@pytest.fixture
def plan(db):
    return MembershipPlan.objects.create(
        name="Standard",
        slug="standard",
        price=Decimal("250.00"),
        currency="ETB",
        duration_months=12,
        loan_limit=3,
    )


@pytest.fixture
def documented_plan(db):
    return MembershipPlan.objects.create(
        name="Researcher",
        slug="researcher",
        price=Decimal("1250.00"),
        currency="ETB",
        duration_months=6,
        loan_limit=10,
        restricted_archive_access=True,
        requires_documents=True,
    )


@pytest.fixture
def guest(db):
    return make_user("guest1", email="guest1@example.org")


@pytest.fixture
def librarian(db):
    return make_user("lib1", ROLE_LIBRARIAN)


def _roles(user) -> set[str]:
    return set(user.user_roles.values_list("role__code", flat=True))


def _actions() -> list[str]:
    return list(AuditRecord.objects.order_by("id").values_list("action", flat=True))


def _request_as(api_client, user, plan_slug: str):
    api_client.force_authenticate(user)
    return api_client.post("/api/v1/membership/requests/", {"plan": plan_slug}, format="json")


def _paid_request(api_client, guest, librarian, plan) -> int:
    request_id = _request_as(api_client, guest, plan.slug).data["id"]
    api_client.force_authenticate(librarian)
    paid = api_client.post(
        f"/api/v1/membership/manage/requests/{request_id}/payment/",
        {"method": "cash", "reference": "RCPT-0001"},
        format="json",
    )
    assert paid.status_code == 200
    return request_id


def test_membership_package_imports():
    import apps.membership as app

    assert app.__name__ == "apps.membership"


# ---- Plans (ILMDAS-553) ----


@pytest.mark.django_db
def test_manager_creates_edits_and_retires_a_plan(api_client):
    api_client.force_authenticate(make_user("mgr", ROLE_MANAGER))
    created = api_client.post(
        "/api/v1/membership/manage/plans/",
        {
            "name": "Student",
            "slug": "student",
            "price": "100.00",
            "currency": "ETB",
            "duration_months": 12,
            "loan_limit": 2,
        },
        format="json",
    )
    assert created.status_code == 201
    assert created.data["price_display"] == "ETB 100.00"
    plan_id = created.data["id"]

    edited = api_client.patch(
        f"/api/v1/membership/manage/plans/{plan_id}/", {"price": "120.00"}, format="json"
    )
    assert edited.status_code == 200
    retired = api_client.patch(
        f"/api/v1/membership/manage/plans/{plan_id}/", {"is_active": False}, format="json"
    )
    assert retired.status_code == 200
    assert MembershipPlan.objects.get(pk=plan_id).is_active is False
    assert _actions() == [
        "membership.plan.created",
        "membership.plan.updated",
        "membership.plan.updated",
        "membership.plan.retired",
    ]

    deleted = api_client.delete(f"/api/v1/membership/manage/plans/{plan_id}/")
    assert deleted.status_code == 405  # plans are retired, never deleted


@pytest.mark.django_db
@pytest.mark.parametrize("payload", [{"price": "-1"}, {"duration_months": 0}, {"currency": "EUR"}])
def test_plan_values_are_validated(api_client, payload):
    api_client.force_authenticate(make_user("mgr", ROLE_MANAGER))
    response = api_client.post(
        "/api/v1/membership/manage/plans/",
        {
            "name": "Bad",
            "slug": "bad",
            "price": "10.00",
            "currency": "ETB",
            "duration_months": 1,
            **payload,
        },
        format="json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
@pytest.mark.parametrize("roles", [(), (ROLE_LIBRARIAN,), (ROLE_JOURNAL_EDITOR,)])
def test_only_managers_and_administrators_manage_plans(api_client, roles):
    api_client.force_authenticate(make_user("someone", *roles))
    response = api_client.post(
        "/api/v1/membership/manage/plans/",
        {"name": "X", "slug": "x", "price": "1", "currency": "ETB", "duration_months": 1},
        format="json",
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_public_plan_list_shows_active_plans_with_formatted_prices(api_client, plan):
    MembershipPlan.objects.create(
        name="Old", slug="old", price=Decimal("5"), duration_months=1, is_active=False
    )
    MembershipPlan.objects.create(
        name="Global", slug="global", price=Decimal("1500"), currency="USD", duration_months=12
    )
    response = api_client.get("/api/v1/membership/plans/")
    assert response.status_code == 200
    by_slug = {item["slug"]: item for item in response.data}
    assert set(by_slug) == {"standard", "global"}
    assert by_slug["standard"]["price_display"] == "ETB 250.00"
    assert by_slug["global"]["price_display"] == "USD 1,500.00"
    assert "is_active" not in by_slug["standard"]


@pytest.mark.django_db
def test_retired_plan_cannot_be_requested(api_client, guest, plan):
    plan.is_active = False
    plan.save()
    response = _request_as(api_client, guest, plan.slug)
    assert response.status_code == 400
    assert not MembershipRequest.objects.exists()


# ---- Requests (ILMDAS-554) ----


@pytest.mark.django_db
def test_guest_requests_a_plan_at_its_current_price(api_client, guest, plan):
    response = _request_as(api_client, guest, plan.slug)
    assert response.status_code == 201
    assert response.data["status"] == MembershipRequest.Status.AWAITING_PAYMENT
    assert response.data["amount"] == "250.00"

    plan.price = Decimal("300.00")
    plan.save()
    assert MembershipRequest.objects.get().amount == Decimal("250.00")
    assert _actions() == ["membership.requested"]


@pytest.mark.django_db
def test_one_open_request_per_account(api_client, guest, plan, documented_plan):
    assert _request_as(api_client, guest, plan.slug).status_code == 201
    second = _request_as(api_client, guest, documented_plan.slug)
    assert second.status_code == 409
    assert second.data["errors"] == ["You already have a membership request in progress."]


@pytest.mark.django_db
def test_unknown_plan_is_rejected(api_client, guest):
    assert _request_as(api_client, guest, "nope").status_code == 400


@pytest.mark.django_db
def test_anonymous_cannot_request_membership(api_client, plan):
    response = api_client.post("/api/v1/membership/requests/", {"plan": "standard"}, format="json")
    assert response.status_code in (401, 403)


# ---- Documents ----


@pytest.mark.django_db
def test_guest_uploads_a_document_to_their_request(api_client, guest, documented_plan):
    request_id = _request_as(api_client, guest, documented_plan.slug).data["id"]
    response = api_client.post(
        f"/api/v1/membership/requests/{request_id}/documents/",
        {"file": SimpleUploadedFile("id-card.pdf", PDF_BYTES)},
        format="multipart",
    )
    assert response.status_code == 201
    assert response.data["content_type"] == "application/pdf"
    assert response.data["original_name"] == "id-card.pdf"
    assert len(FakeStorage.stored) == 1
    assert FakeStorage.stored[0].startswith(f"membership/requests/{request_id}/")
    assert "membership.document_uploaded" in _actions()


@pytest.mark.django_db
def test_document_type_is_checked_from_the_file_content(api_client, guest, documented_plan):
    request_id = _request_as(api_client, guest, documented_plan.slug).data["id"]
    response = api_client.post(
        f"/api/v1/membership/requests/{request_id}/documents/",
        {"file": SimpleUploadedFile("looks-like.pdf", b"just some text")},
        format="multipart",
    )
    assert response.status_code == 400
    assert "file" in response.data["errors"]
    assert FakeStorage.stored == []


@pytest.mark.django_db
def test_missing_file_is_a_validation_error(api_client, guest, documented_plan):
    request_id = _request_as(api_client, guest, documented_plan.slug).data["id"]
    response = api_client.post(
        f"/api/v1/membership/requests/{request_id}/documents/", {}, format="multipart"
    )
    assert response.status_code == 400
    assert response.data["errors"] == {"file": ["Attach a file."]}


@pytest.mark.django_db
def test_cannot_upload_to_another_accounts_request(api_client, guest, documented_plan):
    request_id = _request_as(api_client, guest, documented_plan.slug).data["id"]
    api_client.force_authenticate(make_user("other"))
    response = api_client.post(
        f"/api/v1/membership/requests/{request_id}/documents/",
        {"file": SimpleUploadedFile("id.png", PNG_BYTES)},
        format="multipart",
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_storage_failure_is_reported_as_unavailable(api_client, guest, documented_plan):
    request_id = _request_as(api_client, guest, documented_plan.slug).data["id"]
    FakeStorage.fail = True
    response = api_client.post(
        f"/api/v1/membership/requests/{request_id}/documents/",
        {"file": SimpleUploadedFile("id.pdf", PDF_BYTES)},
        format="multipart",
    )
    assert response.status_code == 503


@pytest.mark.django_db
def test_document_count_is_limited(api_client, guest, documented_plan, monkeypatch):
    monkeypatch.setattr(services, "MAX_DOCUMENTS_PER_REQUEST", 1)
    request_id = _request_as(api_client, guest, documented_plan.slug).data["id"]
    url = f"/api/v1/membership/requests/{request_id}/documents/"
    first = api_client.post(
        url, {"file": SimpleUploadedFile("a.pdf", PDF_BYTES)}, format="multipart"
    )
    second = api_client.post(
        url, {"file": SimpleUploadedFile("b.pdf", PDF_BYTES)}, format="multipart"
    )
    assert first.status_code == 201
    assert second.status_code == 409


# ---- Payment, approval and rejection ----


@pytest.mark.django_db
def test_paid_request_is_approved_and_the_guest_becomes_a_member(
    api_client, guest, librarian, plan
):
    request_id = _paid_request(api_client, guest, librarian, plan)
    assert MembershipRequest.objects.get().status == MembershipRequest.Status.AWAITING_APPROVAL
    assert ROLE_MEMBER not in _roles(guest)

    approved = api_client.post(f"/api/v1/membership/manage/requests/{request_id}/approve/")
    assert approved.status_code == 200
    assert approved.data["status"] == MembershipRequest.Status.APPROVED

    guest.refresh_from_db()
    assert _roles(guest) == {ROLE_GUEST, ROLE_MEMBER}
    assert guest.is_member is True
    subscription = MembershipSubscription.objects.get(user=guest)
    assert subscription.ends_at == services.add_months(subscription.starts_at, 12)
    assert _actions() == [
        "membership.requested",
        "membership.payment_recorded",
        "membership.approved",
        "role.assigned",
    ]

    api_client.force_authenticate(guest)
    mine = api_client.get("/api/v1/membership/me/")
    assert mine.data["isMember"] is True
    assert mine.data["subscription"]["plan"]["slug"] == "standard"


@pytest.mark.django_db
def test_unpaid_request_cannot_be_approved(api_client, guest, librarian, plan):
    request_id = _request_as(api_client, guest, plan.slug).data["id"]
    api_client.force_authenticate(librarian)
    response = api_client.post(f"/api/v1/membership/manage/requests/{request_id}/approve/")
    assert response.status_code == 409
    assert ROLE_MEMBER not in _roles(guest)


@pytest.mark.django_db
def test_payment_is_recorded_once(api_client, guest, librarian, plan):
    request_id = _paid_request(api_client, guest, librarian, plan)
    again = api_client.post(
        f"/api/v1/membership/manage/requests/{request_id}/payment/",
        {"method": "cash", "reference": "RCPT-0002"},
        format="json",
    )
    assert again.status_code == 409
    assert MembershipRequest.objects.get().payment_reference == "RCPT-0001"


@pytest.mark.django_db
def test_plan_with_documents_needs_a_document_before_approval(
    api_client, guest, librarian, documented_plan
):
    request_id = _paid_request(api_client, guest, librarian, documented_plan)
    blocked = api_client.post(f"/api/v1/membership/manage/requests/{request_id}/approve/")
    assert blocked.status_code == 409
    assert blocked.data["errors"] == ["This plan requires documents, and none have been uploaded."]

    api_client.force_authenticate(guest)
    api_client.post(
        f"/api/v1/membership/requests/{request_id}/documents/",
        {"file": SimpleUploadedFile("id.pdf", PDF_BYTES)},
        format="multipart",
    )
    api_client.force_authenticate(librarian)
    approved = api_client.post(f"/api/v1/membership/manage/requests/{request_id}/approve/")
    assert approved.status_code == 200
    assert ROLE_MEMBER in _roles(guest)


@pytest.mark.django_db
def test_rejection_records_the_reason_and_the_account_stays_a_guest(
    api_client, guest, librarian, plan
):
    request_id = _paid_request(api_client, guest, librarian, plan)
    missing_reason = api_client.post(
        f"/api/v1/membership/manage/requests/{request_id}/reject/", {"reason": "  "}, format="json"
    )
    assert missing_reason.status_code == 400

    rejected = api_client.post(
        f"/api/v1/membership/manage/requests/{request_id}/reject/",
        {"reason": "The ID document has expired."},
        format="json",
    )
    assert rejected.status_code == 200
    assert rejected.data["rejection_reason"] == "The ID document has expired."
    assert _roles(guest) == {ROLE_GUEST}
    audit = AuditRecord.objects.get(action="membership.rejected")
    assert audit.details["was_paid"] is True

    # A decided request is closed, so the guest may apply again.
    assert _request_as(api_client, guest, plan.slug).status_code == 201


@pytest.mark.django_db
def test_decided_request_cannot_be_decided_again(api_client, guest, librarian, plan):
    request_id = _paid_request(api_client, guest, librarian, plan)
    api_client.post(f"/api/v1/membership/manage/requests/{request_id}/approve/")
    reject = api_client.post(
        f"/api/v1/membership/manage/requests/{request_id}/reject/",
        {"reason": "Too late"},
        format="json",
    )
    assert reject.status_code == 409


@pytest.mark.django_db
def test_current_member_cannot_open_a_new_request(api_client, guest, librarian, plan):
    request_id = _paid_request(api_client, guest, librarian, plan)
    api_client.post(f"/api/v1/membership/manage/requests/{request_id}/approve/")
    again = _request_as(api_client, guest, plan.slug)
    assert again.status_code == 409


# ---- Approval queue ----


@pytest.mark.django_db
@pytest.mark.parametrize(
    "roles", [(ROLE_LIBRARIAN,), (ROLE_MANAGER,), (ROLE_SYSTEM_ADMINISTRATOR,)]
)
def test_approver_roles_see_the_queue(api_client, guest, librarian, plan, roles):
    _paid_request(api_client, guest, librarian, plan)
    api_client.force_authenticate(make_user("approver", *roles))
    response = api_client.get("/api/v1/membership/manage/requests/")
    assert response.status_code == 200
    assert [item["user"]["username"] for item in response.data] == ["guest1"]


@pytest.mark.django_db
@pytest.mark.parametrize("roles", [(), (ROLE_JOURNAL_EDITOR,)])
def test_other_roles_cannot_use_the_queue(api_client, guest, librarian, plan, roles):
    request_id = _paid_request(api_client, guest, librarian, plan)
    api_client.force_authenticate(make_user("nope", *roles))
    assert api_client.get("/api/v1/membership/manage/requests/").status_code == 403
    approve = api_client.post(f"/api/v1/membership/manage/requests/{request_id}/approve/")
    assert approve.status_code == 403


@pytest.mark.django_db
def test_queue_filters_by_status(api_client, guest, librarian, plan):
    _request_as(api_client, guest, plan.slug)
    api_client.force_authenticate(librarian)
    awaiting_payment = api_client.get("/api/v1/membership/manage/requests/?status=awaiting_payment")
    assert len(awaiting_payment.data) == 1
    assert api_client.get("/api/v1/membership/manage/requests/").data == []
    bad = api_client.get("/api/v1/membership/manage/requests/?status=bogus")
    assert bad.status_code == 400


# ---- Expiry ----


@pytest.mark.django_db
def test_expiry_removes_the_member_role(api_client, guest, librarian, plan):
    request_id = _paid_request(api_client, guest, librarian, plan)
    api_client.post(f"/api/v1/membership/manage/requests/{request_id}/approve/")
    subscription = MembershipSubscription.objects.get()

    after_end = subscription.ends_at + timedelta(seconds=1)
    assert services.expire_memberships(now=after_end) == 1
    assert _roles(guest) == {ROLE_GUEST}
    subscription.refresh_from_db()
    assert subscription.expired_at == after_end
    assert AuditRecord.objects.get(action="membership.expired").details["member_role_removed"]

    assert services.expire_memberships(now=after_end) == 0  # idempotent


@pytest.mark.django_db
def test_expiry_keeps_the_role_while_another_subscription_is_current(guest, plan):
    services_now = timezone.now()
    old_request = MembershipRequest.objects.create(
        user=guest, plan=plan, amount=plan.price, currency=plan.currency, status="approved"
    )
    new_request = MembershipRequest.objects.create(
        user=guest, plan=plan, amount=plan.price, currency=plan.currency, status="approved"
    )
    MembershipSubscription.objects.create(
        user=guest,
        plan=plan,
        request=old_request,
        starts_at=services_now - timedelta(days=40),
        ends_at=services_now - timedelta(days=1),
    )
    MembershipSubscription.objects.create(
        user=guest,
        plan=plan,
        request=new_request,
        starts_at=services_now - timedelta(days=1),
        ends_at=services_now + timedelta(days=30),
    )
    make_user("x")  # roles seeded
    from apps.accounts.models import Role, UserRole

    UserRole.objects.create(user=guest, role=Role.objects.get(code=ROLE_MEMBER))

    assert services.expire_memberships() == 1
    assert ROLE_MEMBER in _roles(guest)


@pytest.mark.django_db
def test_expire_memberships_command(guest, plan):
    out = StringIO()
    call_command("expire_memberships", stdout=out)
    assert out.getvalue().strip() == "Expired 0 membership(s)."


@pytest.mark.parametrize(
    ("start", "months", "end"),
    [
        (
            datetime(2026, 1, 31, tzinfo=UTC),
            1,
            datetime(2026, 2, 28, tzinfo=UTC),
        ),
        (
            datetime(2028, 1, 31, tzinfo=UTC),
            1,
            datetime(2028, 2, 29, tzinfo=UTC),
        ),
        (
            datetime(2026, 11, 15, tzinfo=UTC),
            3,
            datetime(2027, 2, 15, tzinfo=UTC),
        ),
        (
            datetime(2026, 6, 1, tzinfo=UTC),
            12,
            datetime(2027, 6, 1, tzinfo=UTC),
        ),
    ],
)
def test_add_months(start, months, end):
    assert services.add_months(start, months) == end


# ---- Member-only permission (ILMDAS-550) ----


class _MemberOnlyView(APIView):
    permission_classes = [IsMember]

    def get(self, request):
        return Response({"ok": True})


@pytest.mark.django_db
def test_guests_are_denied_member_only_endpoints():
    factory = APIRequestFactory()
    view = _MemberOnlyView.as_view()

    guest_request = factory.get("/member-only/")
    force_authenticate(guest_request, user=make_user("g"))
    assert view(guest_request).status_code == 403

    member_request = factory.get("/member-only/")
    force_authenticate(member_request, user=make_user("m", ROLE_MEMBER))
    assert view(member_request).status_code == 200

    anonymous_request = factory.get("/member-only/")
    assert view(anonymous_request).status_code in (401, 403)
