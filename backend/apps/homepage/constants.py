"""Language and role constants for the public website (FR-WEB-001..005)."""

from __future__ import annotations

from apps.accounts.constants import ROLE_MANAGER, ROLE_SYSTEM_ADMINISTRATOR

# ILMDAS languages from the SRS. Translation overrides are keyed by these codes.
SUPPORTED_LANGUAGES = ("en", "om", "am")
DEFAULT_LANGUAGE = "en"

# Only approved institutional users may manage public website content.
WEBSITE_CONTENT_ROLES = (ROLE_SYSTEM_ADMINISTRATOR, ROLE_MANAGER)
