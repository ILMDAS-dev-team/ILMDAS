"""Role-based permission classes derived from the DEC-019 role matrix."""

from __future__ import annotations

from rest_framework.permissions import BasePermission

from apps.accounts.models import Role


class IsMember(BasePermission):
    """Allows access to any signed-in member."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class CanUploadArchiveObject(BasePermission):
    """Allows uploading archive objects only to Archivists and Administrators."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return (
            getattr(request.user, "role", None) in (Role.ARCHIVIST, Role.ADMINISTRATOR)
            or request.user.is_superuser
        )


class CanViewObjectDetail(BasePermission):
    """Allows viewing object details only to Library Staff, Archivists, and Administrators."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return (
            getattr(request.user, "role", None)
            in (Role.LIBRARY_STAFF, Role.ARCHIVIST, Role.ADMINISTRATOR)
            or request.user.is_superuser
        )


class CanViewMemberRecord(BasePermission):
    """Allows staff to read member records, including the eligibility explanation."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return (
            getattr(request.user, "role", None) in (Role.LIBRARY_STAFF, Role.ADMINISTRATOR)
            or request.user.is_superuser
        )


class CanManageSearchIndex(BasePermission):
    """Allows managing (rebuilding or deleting) the search index only to Administrators."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return (
            getattr(request.user, "role", None) == Role.ADMINISTRATOR or request.user.is_superuser
        )
