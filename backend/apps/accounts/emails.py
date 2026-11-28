"""Account emails: staff invites and email verification (ILMDAS-551, 552).

Emails go through Django's configured email backend, which is the provider adapter
(the provider itself is decision ILMDAS-119). Links point at the Next.js frontend,
which posts the uid and token back to the API.
"""

from __future__ import annotations

from urllib.parse import urlencode

from django.conf import settings
from django.core.mail import send_mail

from .models import User
from .tokens import email_verification_tokens, encode_uid, staff_invite_tokens


def _link(path: str, user: User, token: str) -> str:
    query = urlencode({"uid": encode_uid(user), "token": token})
    return f"{settings.FRONTEND_BASE_URL}{path}?{query}"


def _greeting(user: User) -> str:
    return f"Hello {user.first_name or user.username},"


def send_staff_invite(user: User) -> None:
    """Invite a new staff member to set their own password."""
    link = _link("/accept-invite", user, staff_invite_tokens.make_token(user))
    send_mail(
        subject="Your ILMDAS staff account",
        message=(
            f"{_greeting(user)}\n\n"
            "An ILMDAS administrator has created a staff account for you "
            f"(username: {user.username}).\n\n"
            f"Set your password here:\n{link}\n\n"
            "The link can be used once and expires in a few days. If you were not "
            "expecting this email, you can ignore it."
        ),
        from_email=None,
        recipient_list=[user.email],
    )


def send_email_verification(user: User) -> None:
    """Ask a self-registered user to verify their email address."""
    link = _link("/verify-email", user, email_verification_tokens.make_token(user))
    send_mail(
        subject="Verify your ILMDAS account",
        message=(
            f"{_greeting(user)}\n\n"
            "Thank you for registering with ILMDAS. Verify your email address to "
            f"activate your account:\n{link}\n\n"
            "The link can be used once and expires in a few days. If you did not "
            "register, you can ignore this email."
        ),
        from_email=None,
        recipient_list=[user.email],
    )
