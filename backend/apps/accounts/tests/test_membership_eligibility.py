"""Membership eligibility tests (FR-MEM-004, UC-05, UC-06, ref MEM-02)."""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import (
    Membership,
    MembershipCategory,
    Role,
    User,
    UserAccountStatus,
)
from apps.accounts.services import (
    EligibilityReason,
    MemberNotEligible,
    evaluate_member_eligibility,
    require_member_eligible,
)

PASSWORD = "Test@123456!"  # pragma: allowlist secret


def _member(
    *,
    username: str = "member",
    status: str = UserAccountStatus.ACTIVE,
    category_active: bool = True,
) -> User:
    category = MembershipCategory.objects.create(
        code=f"category-{username}",
        name=f"Category {username}",
        is_active=category_active,
    )
    member = User.objects.create_user(
        username=username,
        password=PASSWORD,
        status=status,
    )
    Membership.objects.create(user=member, category=category)
    return member


@pytest.mark.django_db
def test_mem_02_active_member_in_active_category_is_eligible():
    member = _member()

    result = evaluate_member_eligibility(member)

    assert result.eligible is True
    assert result.reason is None
    assert result.message.startswith("Eligible to borrow.")
    assert result.as_dict() == {
        "eligible": True,
        "reason": None,
        "message": result.message,
    }


@pytest.mark.django_db
def test_mem_02_suspended_member_is_ineligible_with_reason():
    member = _member(status=UserAccountStatus.SUSPENDED)

    result = evaluate_member_eligibility(member)

    assert result.eligible is False
    assert result.reason == EligibilityReason.MEMBER_SUSPENDED
    assert result.as_dict()["reason"] == "member_suspended"
    assert "suspended" in result.message


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("status", "reason"),
    [
        (UserAccountStatus.PENDING, EligibilityReason.MEMBER_INCOMPLETE),
        (UserAccountStatus.DEACTIVATED, EligibilityReason.MEMBER_DEACTIVATED),
        (UserAccountStatus.INACTIVE, EligibilityReason.MEMBER_INACTIVE),
    ],
)
def test_mem_02_incomplete_deactivated_and_inactive_members_are_denied(status, reason):
    member = _member(username=f"member-{status}", status=status)

    result = evaluate_member_eligibility(member)

    assert result.eligible is False
    assert result.reason == reason


@pytest.mark.django_db
def test_mem_02_member_without_membership_record_is_incomplete():
    member = User.objects.create_user(username="no-membership", password=PASSWORD)

    result = evaluate_member_eligibility(member)

    assert result.eligible is False
    assert result.reason == EligibilityReason.MEMBERSHIP_MISSING
    assert "No membership record" in result.message


@pytest.mark.django_db
def test_mem_02_inactive_category_blocks_borrowing():
    member = _member(category_active=False)

    result = evaluate_member_eligibility(member)

    assert result.eligible is False
    assert result.reason == EligibilityReason.CATEGORY_INACTIVE


def test_mem_02_missing_member_is_reported():
    result = evaluate_member_eligibility(None)

    assert result.eligible is False
    assert result.reason == EligibilityReason.MEMBER_NOT_FOUND


@pytest.mark.django_db
def test_require_member_eligible_raises_with_machine_readable_reason():
    member = _member(username="blocked", status=UserAccountStatus.SUSPENDED)

    with pytest.raises(MemberNotEligible) as raised:
        require_member_eligible(member)

    assert raised.value.result.reason == EligibilityReason.MEMBER_SUSPENDED
    assert raised.value.code == "member_suspended"


@pytest.mark.django_db
def test_staff_member_record_includes_staff_language_explanation():
    member = _member(username="suspended-member", status=UserAccountStatus.SUSPENDED)
    staff = User.objects.create_user(
        username="desk-staff",
        password=PASSWORD,
        role=Role.LIBRARY_STAFF,
    )
    client = APIClient()
    client.force_authenticate(staff)

    response = client.get(f"/api/v1/members/{member.id}/")

    assert response.status_code == 200
    assert response.data["borrowingEligibility"]["eligible"] is False
    assert response.data["borrowingEligibility"]["reason"] == "member_suspended"
    assert "suspended" in response.data["borrowingEligibility"]["message"]
    assert response.data["membership"]["category"]["name"] == "Category suspended-member"


@pytest.mark.django_db
def test_member_record_and_reason_are_not_available_to_the_member_or_public():
    member = _member(username="private-member", status=UserAccountStatus.SUSPENDED)
    client = APIClient()

    client.force_authenticate(member)
    forbidden = client.get(f"/api/v1/members/{member.id}/")
    assert forbidden.status_code == 403
    assert forbidden.data["code"] == "authorization_error"

    session = client.get("/api/v1/auth/session/")
    assert session.status_code == 200
    assert "borrowingEligibility" not in session.data
    assert "membership" not in session.data

    client.force_authenticate(None)
    anonymous = client.get(f"/api/v1/members/{member.id}/")
    assert anonymous.status_code == 401
    assert anonymous.data["code"] == "authentication_error"


@pytest.mark.django_db
def test_staff_member_record_handles_missing_membership_and_missing_user():
    member = User.objects.create_user(username="staff-no-membership", password=PASSWORD)
    staff = User.objects.create_user(
        username="admin-viewer",
        password=PASSWORD,
        role=Role.ADMINISTRATOR,
    )
    client = APIClient()
    client.force_authenticate(staff)

    response = client.get(f"/api/v1/members/{member.id}/")
    assert response.status_code == 200
    assert response.data["membership"] is None
    assert response.data["borrowingEligibility"]["reason"] == "membership_missing"

    missing = client.get("/api/v1/members/999999/")
    assert missing.status_code == 404
    assert missing.data["code"] == "not_found"
