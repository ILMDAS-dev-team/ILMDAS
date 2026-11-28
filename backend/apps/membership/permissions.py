"""Permission for member-only endpoints (ILMDAS-550)."""

from __future__ import annotations

from rest_framework.permissions import BasePermission


class IsMember(BasePermission):
    """Allow only accounts with the member role. Guests are denied.

    Use this on member-only endpoints, such as borrowing, as they are built.
    """

    message = "This needs a current membership."

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        return bool(user and user.is_authenticated and user.is_member)
