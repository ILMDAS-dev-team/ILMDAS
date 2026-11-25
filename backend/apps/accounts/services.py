"""Membership eligibility rules shared by circulation issue and renewal (FR-MEM-004)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from django.core.exceptions import ValidationError

from .models import Membership, User, UserAccountStatus


class EligibilityReason(StrEnum):
    """Machine-readable reasons a member cannot borrow."""

    MEMBER_NOT_FOUND = "member_not_found"
    MEMBER_INCOMPLETE = "member_incomplete"
    MEMBER_SUSPENDED = "member_suspended"
    MEMBER_DEACTIVATED = "member_deactivated"
    MEMBER_INACTIVE = "member_inactive"
    MEMBERSHIP_MISSING = "membership_missing"
    CATEGORY_INACTIVE = "category_inactive"


@dataclass(frozen=True, slots=True)
class EligibilityResult:
    """Outcome of the single borrowing-eligibility check."""

    eligible: bool
    reason: EligibilityReason | None
    message: str

    def as_dict(self) -> dict[str, bool | str | None]:
        return {
            "eligible": self.eligible,
            "reason": self.reason.value if self.reason is not None else None,
            "message": self.message,
        }


def _eligible() -> EligibilityResult:
    return EligibilityResult(
        eligible=True,
        reason=None,
        message="Eligible to borrow. The membership is active in an active category.",
    )


def _denied(reason: EligibilityReason, message: str) -> EligibilityResult:
    return EligibilityResult(eligible=False, reason=reason, message=message)


def get_membership_for(member: User) -> Membership | None:
    """Return the member record, or ``None`` when registration is incomplete."""
    try:
        return member.membership
    except Membership.DoesNotExist:
        return None


def evaluate_member_eligibility(member: User | None) -> EligibilityResult:
    """Evaluate membership and category status for borrowing.

    This is the only eligibility decision circulation should use. Fine blocks
    and loan counts are deliberately out of scope until those policies exist.
    """
    if member is None:
        return _denied(
            EligibilityReason.MEMBER_NOT_FOUND,
            "Member record not found. Select an existing member before issuing or renewing a loan.",
        )

    if member.status == UserAccountStatus.PENDING:
        return _denied(
            EligibilityReason.MEMBER_INCOMPLETE,
            "Not eligible to borrow. The membership record is incomplete; finish registration first.",
        )
    if member.status == UserAccountStatus.SUSPENDED:
        return _denied(
            EligibilityReason.MEMBER_SUSPENDED,
            "Not eligible to borrow. The membership is suspended; reinstate it before issuing or renewing a loan.",
        )
    if member.status == UserAccountStatus.DEACTIVATED:
        return _denied(
            EligibilityReason.MEMBER_DEACTIVATED,
            "Not eligible to borrow. The membership is deactivated; reactivate the member record first.",
        )
    if member.status != UserAccountStatus.ACTIVE or not member.is_active:
        return _denied(
            EligibilityReason.MEMBER_INACTIVE,
            "Not eligible to borrow. The membership is inactive; activate it before issuing or renewing a loan.",
        )

    membership = get_membership_for(member)
    if membership is None:
        return _denied(
            EligibilityReason.MEMBERSHIP_MISSING,
            "Not eligible to borrow. No membership record is attached to this account; create the member record first.",
        )

    if not membership.category.is_active:
        return _denied(
            EligibilityReason.CATEGORY_INACTIVE,
            "Not eligible to borrow. The membership category is inactive; move the member to an active category first.",
        )

    return _eligible()


class MemberNotEligible(ValidationError):
    """Raised when circulation attempts to issue or renew for an ineligible member."""

    def __init__(self, result: EligibilityResult) -> None:
        self.result = result
        code = result.reason.value if result.reason is not None else None
        super().__init__(result.message, code=code)


def require_member_eligible(member: User | None) -> EligibilityResult:
    """Return the eligibility result or raise ``MemberNotEligible``."""
    result = evaluate_member_eligibility(member)
    if not result.eligible:
        raise MemberNotEligible(result)
    return result
