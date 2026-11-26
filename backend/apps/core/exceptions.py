"""Shared API error body. Responses never include stack traces or secrets."""

from __future__ import annotations

import logging

from django.core.exceptions import SuspiciousOperation
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    NotAuthenticated,
    NotFound,
    PermissionDenied,
    Throttled,
    ValidationError,
)
from rest_framework.response import Response

logger = logging.getLogger("ilmdas.api")

SAFE_MESSAGE = {
    "validation_error": "The request is not valid.",
    "authentication_error": "Authentication is required.",
    # Same wording for unknown user, wrong password and inactive account.
    "invalid_credentials": "Sign-in failed. Check your details and try again.",
    "authorization_error": "You do not have permission to do that.",
    "not_found": "The requested record was not found.",
    "conflict": "The request conflicts with the current record.",
    "rate_limit": "Too many requests. Try again later.",
    "unavailable": "The request could not be completed.",
}


class Conflict(APIException):
    status_code = 409
    default_detail = SAFE_MESSAGE["conflict"]
    default_code = "conflict"


class InvalidCredentials(AuthenticationFailed):
    """Login was refused. Shares the authentication_error code, with its own safe message."""

    default_detail = SAFE_MESSAGE["invalid_credentials"]
    default_code = "authentication_error"


class ServiceUnavailable(APIException):
    status_code = 503
    default_detail = SAFE_MESSAGE["unavailable"]
    default_code = "unavailable"


def classify(exc: Exception) -> tuple[str, int, object | None]:
    if isinstance(exc, ValidationError):
        return "validation_error", 400, exc.detail
    if isinstance(exc, DjangoValidationError):
        errors = exc.message_dict if hasattr(exc, "message_dict") else exc.messages
        return "validation_error", 400, errors
    if isinstance(exc, SuspiciousOperation):
        return "validation_error", 400, None
    if isinstance(exc, NotAuthenticated | AuthenticationFailed):
        return "authentication_error", 401, None
    if isinstance(exc, PermissionDenied):
        return "authorization_error", 403, None
    if isinstance(exc, NotFound | Http404):
        return "not_found", 404, None
    if isinstance(exc, Conflict) or getattr(exc, "status_code", None) == 409:
        return "conflict", 409, None
    if isinstance(exc, Throttled):
        return "rate_limit", 429, None
    status_code = getattr(exc, "status_code", 500)
    if status_code >= 500:
        return "unavailable", 503, None
    return "unavailable", status_code, None


def api_exception_handler(exc: Exception, context: dict) -> Response:
    request = context.get("request")
    correlation_id = getattr(request, "correlation_id", None) or "missing"
    code, status_code, errors = classify(exc)
    logger.info("api_error code=%s correlation_id=%s", code, correlation_id)
    body: dict = {
        "code": code,
        "message": (
            SAFE_MESSAGE["invalid_credentials"]
            if isinstance(exc, InvalidCredentials)
            else SAFE_MESSAGE.get(code, SAFE_MESSAGE["unavailable"])
        ),
        "correlationId": correlation_id,
    }
    if errors is not None:
        body["errors"] = errors
    return Response(body, status=status_code)
