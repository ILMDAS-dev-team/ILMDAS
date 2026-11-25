"""Circulation eligibility enforcement tests (FR-MEM-004, UC-05, UC-06, ref MEM-02)."""

from __future__ import annotations

import pytest
from django.core.exceptions import ValidationError

from apps.accounts.models import Membership, MembershipCategory, User, UserAccountStatus
from apps.accounts.services import EligibilityReason, MemberNotEligible
from apps.circulation.models import Loan, LoanStatus
from apps.circulation.services import issue_loan, renew_loan, return_loan

PASSWORD = "Test@123456!"  # pragma: allowlist secret


def _member(
    *,
    username: str = "borrower",
    status: str = UserAccountStatus.ACTIVE,
    category_active: bool = True,
) -> User:
    category = MembershipCategory.objects.create(
        code=f"category-{username}",
        name=f"Category {username}",
        is_active=category_active,
    )
    member = User.objects.create_user(username=username, password=PASSWORD, status=status)
    Membership.objects.create(user=member, category=category)
    return member


@pytest.mark.django_db
def test_mem_02_issue_loan_for_eligible_member():
    member = _member()

    loan = issue_loan(member=member, item_reference="catalogue-item-1")

    assert loan.pk is not None
    assert loan.status == LoanStatus.ON_LOAN
    assert loan.member == member
    assert loan.renewal_count == 0


@pytest.mark.django_db
def test_mem_02_issue_loan_refuses_suspended_member():
    member = _member(status=UserAccountStatus.SUSPENDED)

    with pytest.raises(MemberNotEligible) as raised:
        issue_loan(member=member, item_reference="catalogue-item-1")

    assert raised.value.result.reason == EligibilityReason.MEMBER_SUSPENDED
    assert Loan.objects.filter(member=member).count() == 0


@pytest.mark.django_db
def test_mem_02_direct_loan_write_cannot_bypass_the_check():
    member = _member(username="direct-write", status=UserAccountStatus.SUSPENDED)

    with pytest.raises(MemberNotEligible) as raised:
        Loan.objects.create(member=member, item_reference="catalogue-item-1")

    assert raised.value.result.reason == EligibilityReason.MEMBER_SUSPENDED
    assert Loan.objects.count() == 0


@pytest.mark.django_db
def test_mem_02_bulk_loan_write_cannot_bypass_the_check():
    member = _member(username="bulk-write", status=UserAccountStatus.DEACTIVATED)

    with pytest.raises(MemberNotEligible) as raised:
        Loan.objects.bulk_create([Loan(member=member, item_reference="catalogue-item-1")])

    assert raised.value.result.reason == EligibilityReason.MEMBER_DEACTIVATED
    assert Loan.objects.count() == 0


@pytest.mark.django_db
def test_mem_02_renewal_rechecks_eligibility_after_suspension():
    member = _member(username="renewal-member")
    loan = issue_loan(member=member, item_reference="catalogue-item-1")
    member.suspend()

    with pytest.raises(MemberNotEligible) as raised:
        renew_loan(loan)

    assert raised.value.result.reason == EligibilityReason.MEMBER_SUSPENDED
    loan.refresh_from_db()
    assert loan.renewal_count == 0


@pytest.mark.django_db
def test_mem_02_renewal_of_eligible_loan_increments_count():
    member = _member(username="eligible-renewal")
    loan = issue_loan(member=member, item_reference="catalogue-item-1")

    renew_loan(loan)

    loan.refresh_from_db()
    assert loan.renewal_count == 1
    assert loan.last_renewed_at is not None


@pytest.mark.django_db
def test_mem_02_returns_are_allowed_when_member_is_later_suspended():
    member = _member(username="return-member")
    loan = issue_loan(member=member, item_reference="catalogue-item-1")
    member.suspend()

    return_loan(loan)

    loan.refresh_from_db()
    assert loan.status == LoanStatus.RETURNED
    assert loan.returned_at is not None


@pytest.mark.django_db
def test_mem_02_closed_loan_cannot_be_renewed_or_returned_twice():
    member = _member(username="closed-loan")
    loan = issue_loan(member=member, item_reference="catalogue-item-1")
    return_loan(loan)

    with pytest.raises(ValidationError):
        renew_loan(loan)
    with pytest.raises(ValidationError):
        return_loan(loan)


@pytest.mark.django_db
def test_mem_02_inactive_category_blocks_direct_write():
    member = _member(username="inactive-category", category_active=False)

    with pytest.raises(MemberNotEligible) as raised:
        Loan.objects.create(member=member, item_reference="catalogue-item-1")

    assert raised.value.result.reason == EligibilityReason.CATEGORY_INACTIVE
