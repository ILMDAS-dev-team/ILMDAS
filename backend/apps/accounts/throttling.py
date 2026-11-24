"""Throttling classes for authentication and upload endpoints."""

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    scope = "login"


class UploadRateThrottle(UserRateThrottle):
    scope = "upload"
