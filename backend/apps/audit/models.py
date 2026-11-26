"""Audit trail models and event recording for ILMDAS."""

from __future__ import annotations

from typing import Any

from django.conf import settings
from django.db import models


class AuditRecord(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_records",
    )
    actor_username = models.CharField(max_length=150, blank=True)
    action = models.CharField(max_length=128, db_index=True)
    object_type = models.CharField(max_length=128, blank=True)
    object_id = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    correlation_id = models.CharField(max_length=64, blank=True)
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["action", "timestamp"]),
            models.Index(fields=["object_type", "object_id"]),
        ]

    def __str__(self) -> str:
        actor = self.actor_username or (self.actor.username if self.actor else "system")
        return f"[{self.timestamp.isoformat()}] {actor} - {self.action} ({self.object_type}:{self.object_id})"


def sanitize_audit_details(data: Any) -> Any:
    """Recursively scrub sensitive fields (passwords, tokens, secrets, credentials, api keys)."""
    if isinstance(data, dict):
        sanitized = {}
        for k, v in data.items():
            normalized_k = str(k).lower().replace("_", "").replace("-", "")
            if any(
                sensitive in normalized_k
                for sensitive in (
                    "password",
                    "secret",
                    "token",
                    "credential",
                    "apikey",
                    "privatekey",
                    "authorization",
                    "cookie",
                    "session",
                    "otp",
                )
            ):
                sanitized[k] = "[REDACTED]"
            else:
                sanitized[k] = sanitize_audit_details(v)
        return sanitized
    if isinstance(data, list):
        return [sanitize_audit_details(item) for item in data]
    return data


def record_audit_event(
    action: str,
    actor: Any = None,
    object_type: str = "",
    object_id: str = "",
    details: dict | None = None,
    request: Any = None,
) -> AuditRecord:
    """Record a security or domain event in the audit trail."""
    actor_obj = None
    actor_name = ""
    ip_address = None
    correlation_id = ""

    if request is not None:
        user = getattr(request, "user", None)
        if user is not None and getattr(user, "is_authenticated", False):
            actor_obj = user
            actor_name = user.get_username()
        ip_address = request.META.get("REMOTE_ADDR")
        correlation_id = getattr(request, "correlation_id", "") or request.headers.get(
            "X-Correlation-ID", ""
        )

    if actor is not None and not actor_obj:
        if hasattr(actor, "is_authenticated") and actor.is_authenticated:
            actor_obj = actor
            actor_name = actor.get_username()
        elif isinstance(actor, str):
            actor_name = actor

    safe_details = sanitize_audit_details(details) if details else {}

    return AuditRecord.objects.create(
        actor=actor_obj,
        actor_username=actor_name,
        action=action,
        object_type=object_type,
        object_id=str(object_id),
        ip_address=ip_address,
        correlation_id=correlation_id,
        details=safe_details,
    )
