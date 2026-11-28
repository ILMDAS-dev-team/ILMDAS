"""Read-only serialization of audit records (ILMDAS-31)."""

from __future__ import annotations

from rest_framework import serializers

from .models import AuditRecord


class AuditRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditRecord
        fields = [
            "id",
            "timestamp",
            "actor_username",
            "action",
            "object_type",
            "object_id",
            "outcome",
            "correlation_id",
            "details",  # sanitized on write by sanitize_audit_details()
        ]
        read_only_fields = fields
