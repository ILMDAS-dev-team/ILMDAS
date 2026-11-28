"""Roles and limits for membership (ILMDAS-553, ILMDAS-554)."""

from __future__ import annotations

from apps.accounts.constants import ROLE_LIBRARIAN, ROLE_MANAGER, ROLE_SYSTEM_ADMINISTRATOR

# Who may create, edit and retire membership plans.
PLAN_MANAGER_ROLES = (ROLE_SYSTEM_ADMINISTRATOR, ROLE_MANAGER)

# Who may record payments and approve or reject membership requests.
MEMBERSHIP_APPROVER_ROLES = (ROLE_SYSTEM_ADMINISTRATOR, ROLE_MANAGER, ROLE_LIBRARIAN)

# Identity and supporting documents uploaded with a membership request.
ALLOWED_DOCUMENT_TYPES = frozenset({"application/pdf", "image/jpeg", "image/png"})
MAX_DOCUMENT_BYTES = 5 * 1024 * 1024
MAX_DOCUMENTS_PER_REQUEST = 5
