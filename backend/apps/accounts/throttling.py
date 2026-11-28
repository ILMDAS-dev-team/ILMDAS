"""Throttling classes for authentication and upload endpoints."""

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    scope = "login"


class UploadRateThrottle(UserRateThrottle):
    scope = "upload"


class RegistrationRateThrottle(AnonRateThrottle):
    """Sign-up, verification resend and invite acceptance (FR-SEC-008, ILMDAS-552)."""

    scope = "registration"
