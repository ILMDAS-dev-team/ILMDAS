"""Circulation loan records with membership eligibility enforced on write (FR-MEM-004)."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.services import require_member_eligible


class LoanStatus(models.TextChoices):
    ON_LOAN = "on_loan", "On loan"
    RETURNED = "returned", "Returned"


class LoanQuerySet(models.QuerySet):
    """Guard bulk writes so a caller cannot bypass the model save check."""

    def bulk_create(
        self,
        objs: Iterable[Loan],
        *args: Any,
        **kwargs: Any,
    ) -> list[Loan]:
        loans = list(objs)
        for loan in loans:
            if loan.status == LoanStatus.ON_LOAN:
                loan.check_borrower_eligibility()
        return super().bulk_create(loans, *args, **kwargs)


class Loan(models.Model):
    """A loan. Loan periods and loan limits stay out until those policies are approved."""

    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="loans",
    )
    item_reference = models.CharField(max_length=255)
    status = models.CharField(
        max_length=32,
        choices=LoanStatus.choices,
        default=LoanStatus.ON_LOAN,
        db_index=True,
    )
    issued_at = models.DateTimeField(default=timezone.now, db_index=True)
    returned_at = models.DateTimeField(null=True, blank=True)
    renewal_count = models.PositiveIntegerField(default=0)
    last_renewed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LoanQuerySet.as_manager()

    class Meta:
        ordering = ["-issued_at"]
        verbose_name = "loan"
        verbose_name_plural = "loans"
        indexes = [
            models.Index(fields=["member", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.member.get_username()} - {self.item_reference} ({self.status})"

    def check_borrower_eligibility(self) -> None:
        """Raise ``MemberNotEligible`` when the member cannot borrow."""
        require_member_eligible(self.member)

    def clean(self) -> None:
        super().clean()
        if self.status == LoanStatus.ON_LOAN:
            self.check_borrower_eligibility()

    def save(self, *args: Any, **kwargs: Any) -> None:
        # This guard is the reason a direct ``Loan.objects.create(...)`` cannot
        # bypass circulation's issue/renewal service.
        if self.status == LoanStatus.ON_LOAN:
            self.check_borrower_eligibility()
        super().save(*args, **kwargs)

    def renew(self, *, renewed_at: datetime | None = None) -> None:
        """Renew an open loan after re-checking the member's eligibility."""
        if self.status != LoanStatus.ON_LOAN:
            raise ValidationError("Only an open loan can be renewed.", code="loan_not_open")
        self.check_borrower_eligibility()
        self.renewal_count += 1
        self.last_renewed_at = renewed_at or timezone.now()
        self.save(update_fields=["renewal_count", "last_renewed_at", "updated_at"])

    def mark_returned(self, *, returned_at: datetime | None = None) -> None:
        """Return an open loan. Returns are allowed even if the member is now blocked."""
        if self.status != LoanStatus.ON_LOAN:
            raise ValidationError("Only an open loan can be returned.", code="loan_not_open")
        self.status = LoanStatus.RETURNED
        self.returned_at = returned_at or timezone.now()
        self.save(update_fields=["status", "returned_at", "updated_at"])


def get_member_loans(member: User):
    """Return the member's loan history, newest first."""
    return Loan.objects.filter(member=member)
