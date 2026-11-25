"""Circulation issue and renewal services (UC-05, UC-06, FR-MEM-004)."""

from __future__ import annotations

from datetime import datetime

from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.services import require_member_eligible

from .models import Loan, LoanStatus


def issue_loan(
    *,
    member: User,
    item_reference: str,
    issued_at: datetime | None = None,
) -> Loan:
    """Issue a loan only after the shared eligibility check passes."""
    require_member_eligible(member)
    loan = Loan(
        member=member,
        item_reference=item_reference,
        status=LoanStatus.ON_LOAN,
        issued_at=issued_at or timezone.now(),
    )
    loan.save(force_insert=True)
    return loan


def renew_loan(loan: Loan, *, renewed_at: datetime | None = None) -> Loan:
    """Renew an existing loan after re-checking the member's eligibility."""
    loan.renew(renewed_at=renewed_at)
    return loan


def return_loan(loan: Loan, *, returned_at: datetime | None = None) -> Loan:
    """Close an open loan."""
    loan.mark_returned(returned_at=returned_at)
    return loan
