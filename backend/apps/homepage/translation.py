"""Helpers for approved translations of website content."""

from __future__ import annotations

from typing import Any

from .constants import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES


def resolve_language(request: Any) -> str:
    """Pick a supported language from `?lang=`, Accept-Language, then the default."""
    requested = ""
    query_params = getattr(request, "query_params", None)
    if query_params is not None:
        requested = query_params.get("lang", "")
    else:
        requested = request.GET.get("lang", "")
    if requested in SUPPORTED_LANGUAGES:
        return requested

    header = request.META.get("HTTP_ACCEPT_LANGUAGE", "") if hasattr(request, "META") else ""
    for part in header.split(","):
        code = part.split(";", 1)[0].strip().lower().replace("_", "-")
        base = code.split("-", 1)[0]
        if base in SUPPORTED_LANGUAGES:
            return base
    return DEFAULT_LANGUAGE


def localized(instance: Any, field: str, language: str) -> str:
    """Return the approved translation for a field, or its untranslated value."""
    value = getattr(instance, field, "") or ""
    translations = getattr(instance, "translations", None)
    if isinstance(translations, dict):
        overrides = translations.get(language)
        if isinstance(overrides, dict):
            translated = overrides.get(field)
            if isinstance(translated, str) and translated:
                return translated
    return value
