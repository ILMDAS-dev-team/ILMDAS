"""Validators that keep public links on approved, same-site destinations."""

from __future__ import annotations

from urllib.parse import urlparse

from django.core.exceptions import ValidationError

LOCAL_PATH_PREFIXES = ("/",)


def validate_local_path(value: str) -> None:
    """Accept only same-site paths such as `/archive/object/123/`."""
    if (
        not value.startswith(LOCAL_PATH_PREFIXES)
        or value.startswith("//")
        or value.startswith("/\\")
    ):
        raise ValidationError("Use a same-site path beginning with a single '/'.")
    if "\n" in value or "\r" in value:
        raise ValidationError("The path must not contain line breaks.")


def validate_link_url(value: str) -> None:
    """Accept a same-site path or an approved external http(s) URL."""
    if value.startswith("/"):
        validate_local_path(value)
        return
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValidationError("Use a same-site path or an https:// URL.")
