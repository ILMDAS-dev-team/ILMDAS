"""Membership plans, requests, documents and subscriptions (ILMDAS-553, ILMDAS-554).

A guest becomes a member by requesting a plan, paying for it and, where the plan needs
it, having their documents approved by staff. Approval creates a subscription and
grants the member role in one transaction; expiry ends both (see ``services``).

Membership plans also serve as the member categories (ILMDAS-33).
"""

from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Currency(models.TextChoices):
    ETB = "ETB", "Ethiopian Birr"
    USD = "USD", "US Dollar"


class MembershipPlan(models.Model):
    """A membership plan: its price, duration and benefits (ILMDAS-553).

    Prices are data, not code. Plan prices are [TBC] in the SRS (ILMDAS-117).
    """

    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0"))]
    )
    currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.ETB)
    duration_months = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    loan_limit = models.PositiveSmallIntegerField(
        default=0, help_text="How many items a member on this plan may borrow at once."
    )
    restricted_archive_access = models.BooleanField(
        default=False, help_text="Whether the plan opens restricted archive content."
    )
    benefits = models.TextField(blank=True, help_text="Other benefits, shown to guests.")
    requires_documents = models.BooleanField(
        default=False, help_text="Whether staff must check uploaded documents before approval."
    )
    is_active = models.BooleanField(
        default=True, help_text="Retired plans cannot be chosen for new requests."
    )
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.price_display})"

    @property
    def price_display(self) -> str:
        """The price with its currency, e.g. ``ETB 1,250.00``."""
        return f"{self.currency} {self.price:,.2f}"


class MembershipRequest(models.Model):
    """A guest's request for a plan, from payment to the staff decision (ILMDAS-554)."""

    class Status(models.TextChoices):
        AWAITING_PAYMENT = "awaiting_payment", "Awaiting payment"
        AWAITING_APPROVAL = "awaiting_approval", "Awaiting approval"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    class PaymentMethod(models.TextChoices):
        CASH = "cash", "Cash"
        BANK_TRANSFER = "bank_transfer", "Bank transfer"
        TELEBIRR = "telebirr", "Telebirr"
        CBE_BIRR = "cbe_birr", "CBE Birr"
        CARD = "card", "VISA / Mastercard"
        OTHER = "other", "Other"

    OPEN_STATUSES = (Status.AWAITING_PAYMENT, Status.AWAITING_APPROVAL)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="membership_requests"
    )
    plan = models.ForeignKey(MembershipPlan, on_delete=models.PROTECT, related_name="requests")
    status = models.CharField(
        max_length=32, choices=Status.choices, default=Status.AWAITING_PAYMENT, db_index=True
    )
    # The price is copied at request time, so a later price change doesn't alter it.
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, choices=Currency.choices)

    payment_method = models.CharField(max_length=32, choices=PaymentMethod.choices, blank=True)
    payment_reference = models.CharField(max_length=128, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    payment_recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(status__in=["awaiting_payment", "awaiting_approval"]),
                name="membership_one_open_request_per_user",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user} -> {self.plan.name} ({self.get_status_display()})"

    @property
    def is_open(self) -> bool:
        return self.status in self.OPEN_STATUSES


class MembershipDocument(models.Model):
    """A document uploaded with a request. The file itself is in object storage."""

    request = models.ForeignKey(
        MembershipRequest, on_delete=models.CASCADE, related_name="documents"
    )
    object_key = models.CharField(max_length=512, unique=True)
    checksum_sha256 = models.CharField(max_length=64)
    content_type = models.CharField(max_length=100)
    original_name = models.CharField(max_length=255)
    size = models.PositiveIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["uploaded_at", "id"]

    def __str__(self) -> str:
        return self.original_name


class MembershipSubscription(models.Model):
    """A membership period created when a request is approved (ILMDAS-554).

    Renewal is ILMDAS-547. ``expired_at`` is set when the period ends and the member
    role is removed.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscriptions"
    )
    plan = models.ForeignKey(MembershipPlan, on_delete=models.PROTECT, related_name="subscriptions")
    request = models.OneToOneField(
        MembershipRequest, on_delete=models.PROTECT, related_name="subscription"
    )
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(db_index=True)
    expired_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-ends_at", "-id"]

    def __str__(self) -> str:
        return f"{self.user} {self.plan.name} until {self.ends_at:%Y-%m-%d}"

    @property
    def is_current(self) -> bool:
        return self.expired_at is None and self.starts_at <= timezone.now() < self.ends_at
