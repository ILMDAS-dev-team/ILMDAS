"""Reusable role-based authorization permissions for ILMDAS."""

from __future__ import annotations

from rest_framework.permissions import BasePermission

from apps.accounts.constants import (
    ROLE_DIGITAL_ARCHIVIST,
    ROLE_INTEGRATION_ADMINISTRATOR,
    ROLE_JOURNAL_EDITOR,
    ROLE_LIBRARIAN,
    ROLE_MANAGER,
    ROLE_MEMBER,
    ROLE_SYSTEM_ADMINISTRATOR,
)


class HasRole(BasePermission):
    """Check that the authenticated user holds a specific role code.

    The view sets ``required_role`` to a role code constant. When unset, any
    authenticated user is permitted. Unauthenticated requests are denied.
    """

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False

        required_role = getattr(view, "required_role", None)
        if required_role is None:
            return True

        return user.user_roles.filter(role__code=required_role).exists()


__all__ = [
    "HasRole",
    "ROLE_SYSTEM_ADMINISTRATOR",
    "ROLE_LIBRARIAN",
    "ROLE_DIGITAL_ARCHIVIST",
    "ROLE_JOURNAL_EDITOR",
    "ROLE_MEMBER",
    "ROLE_MANAGER",
    "ROLE_INTEGRATION_ADMINISTRATOR",
]
