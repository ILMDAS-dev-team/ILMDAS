"""Stored object reference. The binary itself stays in object storage."""

from django.db import models


class ObjectReference(models.Model):
    object_key = models.CharField(max_length=512, unique=True)
    reference = models.CharField(max_length=1024)
    checksum_sha256 = models.CharField(max_length=64)
    content_type = models.CharField(max_length=255, blank=True)
    scan_status = models.CharField(max_length=32, default="pending", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.object_key
