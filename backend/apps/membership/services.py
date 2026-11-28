"""Membership rules: requests, payment, approval, rejection and expiry (ILMDAS-554).

Views stay thin and call these functions. They keep the member role and the
subscription in step: approval grants both in one transaction, and expiry ends both.
So no account holds the member role without a current subscription, unless an
administrator assigns it by hand.

Payment is recorded by staff for now (cash, bank transfer, or a reference from
another channel). ``record_payment`` is the single entry point for "this request is
paid", so the Telebirr, CBE Birr and card integrations (ILMDAS-544 to 546) will call
it from their verified callbacks (ILMDAS-65) instead of adding a second path.
"""

from __future__ import annotations

import calendar
import uuid
from datetime import datetime
from typing import Any

from django.core.files.uploadedfile import UploadedFile
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.accounts.constants import ROLE_MEMBER
from apps.accounts.models import Role, UserRole
from apps.audit.models import record_audit_event
from apps.core.content_type import detect_mime_type
from apps.core.exceptions import Conflict, ServiceUnavailable
from apps.core.storage import ObjectStorage, ObjectStorageError

from .constants import ALLOWED_DOCUMENT_TYPES, MAX_DOCUMENT_BYTES, MAX_DOCUMENTS_PER_REQUEST
from .models import (
    MembershipDocument,
    MembershipPlan,
    MembershipRequest,
    MembershipSubscription,
)


def add_months(moment: datetime, months: int) -> datetime:
    """``moment`` plus whole calendar months, clamping the day (31 Jan + 1 = 28/29 Feb)."""
    month_index = moment.month - 1 + months
    year = moment.year + month_index // 12
    month = month_index % 12 + 1
    day = min(moment.day, calendar.monthrange(year, month)[1])
    return moment.replace(year=year, month=month, day=day)


def current_subscription(user: Any) -> MembershipSubscription | None:
    return (
        MembershipSubscription.objects.filter(
            user=user, expired_at__isnull=True, ends_at__gt=timezone.now()
        )
        .select_related("plan")
        .first()
    )


def _audit(action: str, actor: Any, membership_request: MembershipRequest, request: Any, **details):
    record_audit_event(
        action=action,
        actor=actor,
        object_type="MembershipRequest",
        object_id=str(membership_request.pk),
        details={
            "target_user": membership_request.user.get_username(),
            "plan": membership_request.plan.slug,
            **details,
        },
        request=request,
    )


def create_request(user: Any, plan: MembershipPlan, *, request: Any = None) -> MembershipRequest:
    """A guest asks for a plan. One open request per account at a time."""
    if not plan.is_active:
        raise ValidationError({"plan": ["This plan is no longer available."]})
    if current_subscription(user) is not None:
        raise Conflict("You already have a current membership. Renewal is a separate step.")
    if MembershipRequest.objects.filter(
        user=user, status__in=MembershipRequest.OPEN_STATUSES
    ).exists():
        raise Conflict("You already have a membership request in progress.")
    try:
        with transaction.atomic():
            membership_request = MembershipRequest.objects.create(
                user=user, plan=plan, amount=plan.price, currency=plan.currency
            )
    except IntegrityError:  # a parallel request won the race for the open-request slot
        raise Conflict("You already have a membership request in progress.") from None
    _audit("membership.requested", user, membership_request, request, amount=str(plan.price))
    return membership_request


def upload_document(
    membership_request: MembershipRequest,
    uploaded: UploadedFile,
    *,
    actor: Any,
    request: Any = None,
    storage: ObjectStorage | None = None,
) -> MembershipDocument:
    """Store a supporting document for an open request in private object storage."""
    if not membership_request.is_open:
        raise Conflict("Documents can only be added while the request is in progress.")
    if membership_request.documents.count() >= MAX_DOCUMENTS_PER_REQUEST:
        raise Conflict(f"A request can have at most {MAX_DOCUMENTS_PER_REQUEST} documents.")
    if uploaded.size is None or uploaded.size > MAX_DOCUMENT_BYTES:
        raise ValidationError(
            {"file": [f"The file must be at most {MAX_DOCUMENT_BYTES // (1024 * 1024)} MB."]}
        )
    body = uploaded.read()
    content_type = detect_mime_type(body)
    if content_type not in ALLOWED_DOCUMENT_TYPES:
        raise ValidationError({"file": ["Upload a PDF, JPEG or PNG file."]})

    object_key = f"membership/requests/{membership_request.pk}/{uuid.uuid4().hex}"
    storage = storage or ObjectStorage()
    try:
        stored = storage.put_private(object_key, body, content_type=content_type)
    except ObjectStorageError as exc:
        raise ServiceUnavailable() from exc
    document = MembershipDocument.objects.create(
        request=membership_request,
        object_key=stored.object_key,
        checksum_sha256=stored.checksum_sha256,
        content_type=content_type,
        original_name=(uploaded.name or "document")[:255],
        size=len(body),
    )
    _audit(
        "membership.document_uploaded",
        actor,
        membership_request,
        request,
        document_id=document.pk,
        content_type=content_type,
    )
    return document


def record_payment(
    membership_request: MembershipRequest,
    *,
    method: str,
    reference: str,
    actor: Any,
    request: Any = None,
) -> MembershipRequest:
    """Mark a request as paid. Staff call this today; provider callbacks will later."""
    with transaction.atomic():
        locked = MembershipRequest.objects.select_for_update().get(pk=membership_request.pk)
        if locked.status != MembershipRequest.Status.AWAITING_PAYMENT:
            raise Conflict("This request is not waiting for payment.")
        locked.payment_method = method
        locked.payment_reference = reference
        locked.paid_at = timezone.now()
        locked.payment_recorded_by = actor
        locked.status = MembershipRequest.Status.AWAITING_APPROVAL
        locked.save()
    _audit(
        "membership.payment_recorded",
        actor,
        locked,
        request,
        method=method,
        reference=reference,
        amount=str(locked.amount),
        currency=locked.currency,
    )
    return locked


def approve(membership_request: MembershipRequest, *, actor: Any, request: Any = None):
    """Approve a paid request: start the subscription and grant the member role."""
    with transaction.atomic():
        locked = (
            MembershipRequest.objects.select_for_update()
            .select_related("plan", "user")
            .get(pk=membership_request.pk)
        )
        if locked.status != MembershipRequest.Status.AWAITING_APPROVAL:
            raise Conflict("Only a paid request that is awaiting approval can be approved.")
        if locked.plan.requires_documents and not locked.documents.exists():
            raise Conflict("This plan requires documents, and none have been uploaded.")

        now = timezone.now()
        subscription = MembershipSubscription.objects.create(
            user=locked.user,
            plan=locked.plan,
            request=locked,
            starts_at=now,
            ends_at=add_months(now, locked.plan.duration_months),
        )
        member_role = Role.objects.get(code=ROLE_MEMBER)
        UserRole.objects.get_or_create(
            user=locked.user, role=member_role, defaults={"assigned_by": actor}
        )
        locked.status = MembershipRequest.Status.APPROVED
        locked.decided_by = actor
        locked.decided_at = now
        locked.save()

        _audit(
            "membership.approved",
            actor,
            locked,
            request,
            subscription_id=subscription.pk,
            ends_at=subscription.ends_at.isoformat(),
        )
        record_audit_event(
            action="role.assigned",
            actor=actor,
            object_type="UserRole",
            object_id=str(locked.user.pk),
            details={
                "target_user": locked.user.get_username(),
                "role_code": member_role.code,
                "role_name": member_role.name,
                "via": "membership_approval",
            },
            request=request,
        )
    return locked, subscription


def reject(
    membership_request: MembershipRequest, *, actor: Any, reason: str, request: Any = None
) -> MembershipRequest:
    """Reject an open request with a reason. The account stays a guest.

    If the request was already paid, the refund follows the rules decided in ILMDAS-118;
    the audit record notes whether a payment had been recorded.
    """
    reason = reason.strip()
    if not reason:
        raise ValidationError({"reason": ["Give a reason for the rejection."]})
    with transaction.atomic():
        locked = MembershipRequest.objects.select_for_update().get(pk=membership_request.pk)
        if not locked.is_open:
            raise Conflict("This request has already been decided.")
        was_paid = locked.paid_at is not None
        locked.status = MembershipRequest.Status.REJECTED
        locked.rejection_reason = reason
        locked.decided_by = actor
        locked.decided_at = timezone.now()
        locked.save()
    _audit("membership.rejected", actor, locked, request, reason=reason, was_paid=was_paid)
    return locked


def expire_memberships(now: datetime | None = None) -> int:
    """End every subscription whose period is over, and remove the member role.

    Idempotent: an already-expired subscription is skipped. The member role stays if
    the account has another current subscription. Returns how many were expired.
    """
    now = now or timezone.now()
    expired = 0
    due = MembershipSubscription.objects.filter(
        expired_at__isnull=True, ends_at__lte=now
    ).select_related("user", "plan")
    for subscription in due:
        with transaction.atomic():
            subscription.expired_at = now
            subscription.save(update_fields=["expired_at"])
            still_current = (
                MembershipSubscription.objects.filter(
                    user=subscription.user, expired_at__isnull=True, ends_at__gt=now
                )
                .exclude(pk=subscription.pk)
                .exists()
            )
            role_removed = False
            if not still_current:
                deleted, _ = UserRole.objects.filter(
                    user=subscription.user, role__code=ROLE_MEMBER
                ).delete()
                role_removed = deleted > 0
            record_audit_event(
                action="membership.expired",
                actor="system",
                object_type="MembershipSubscription",
                object_id=str(subscription.pk),
                details={
                    "target_user": subscription.user.get_username(),
                    "plan": subscription.plan.slug,
                    "member_role_removed": role_removed,
                },
            )
        expired += 1
    return expired
