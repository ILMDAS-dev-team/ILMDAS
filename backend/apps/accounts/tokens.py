"""Signed one-time links for staff invites and email verification (ILMDAS-551, 552).

The tokens use Django's password-reset token machinery: no token table is needed,
they expire after ``PASSWORD_RESET_TIMEOUT`` seconds, and they stop working as soon
as the account changes. The hash includes the password hash and the account status,
so setting a password or activating the account invalidates the link (single use).
"""

from __future__ import annotations

from typing import Any

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework.exceptions import ValidationError

from .models import User, UserAccountStatus

INVALID_LINK_MESSAGE = "This link is invalid or has expired."


class _AccountLinkTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user: Any, timestamp: int) -> str:
        return f"{user.pk}{user.password}{user.status}{user.email}{timestamp}"


class StaffInviteTokenGenerator(_AccountLinkTokenGenerator):
    key_salt = "apps.accounts.tokens.StaffInviteTokenGenerator"


class EmailVerificationTokenGenerator(_AccountLinkTokenGenerator):
    key_salt = "apps.accounts.tokens.EmailVerificationTokenGenerator"


staff_invite_tokens = StaffInviteTokenGenerator()
email_verification_tokens = EmailVerificationTokenGenerator()


def encode_uid(user: User) -> str:
    return urlsafe_base64_encode(force_bytes(user.pk))


def pending_user_from_link(uid: str, token: str, generator: PasswordResetTokenGenerator) -> User:
    """Return the pending account a link belongs to, or raise one generic error."""
    try:
        user = User.objects.get(pk=force_str(urlsafe_base64_decode(uid)))
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        raise ValidationError({"token": [INVALID_LINK_MESSAGE]}) from None
    if user.status != UserAccountStatus.PENDING or not generator.check_token(user, token):
        raise ValidationError({"token": [INVALID_LINK_MESSAGE]})
    return user
