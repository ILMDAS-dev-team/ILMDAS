"""Role-based permission classes derived from the DEC-019 role matrix."""

from __future__ import annotations

from rest_framework.permissions import BasePermission

from apps.accounts.constants import (
    ROLE_DIGITAL_ARCHIVIST,
    ROLE_LIBRARIAN,
    ROLE_SYSTEM_ADMINISTRATOR,
)


def _has_any_role(request, *codes: str) -> bool:
    user = request.user
    if not (user and user.is_authenticated):
        return False
    return user.is_superuser or user.has_any_role(*codes)


class IsMember(BasePermission):
    """Allows access to any signed-in member."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class CanUploadArchiveObject(BasePermission):
    """Allows uploading archive objects only to Archivists and Administrators."""

    def has_permission(self, request, view):
        return _has_any_role(request, ROLE_SYSTEM_ADMINISTRATOR, ROLE_DIGITAL_ARCHIVIST)


class CanViewObjectDetail(BasePermission):
    """Allows viewing object details only to Library Staff, Archivists, and Administrators."""

    def has_permission(self, request, view):
        return _has_any_role(
            request, ROLE_SYSTEM_ADMINISTRATOR, ROLE_LIBRARIAN, ROLE_DIGITAL_ARCHIVIST
        )


class CanManageSearchIndex(BasePermission):
    """Allows managing (rebuilding or deleting) the search index only to Administrators."""

    def has_permission(self, request, view):
        return _has_any_role(request, ROLE_SYSTEM_ADMINISTRATOR)
