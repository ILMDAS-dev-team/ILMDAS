"""Magic byte inspection and content validation for upload controls (SEC-09)."""

from __future__ import annotations

import json

from rest_framework.exceptions import ValidationError

MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB limit

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/tiff",
    "image/gif",
    "application/zip",
    "text/plain",
    "application/json",
    "application/xml",
}


def detect_mime_type(body: bytes) -> str:
    """Inspect magic bytes to determine the actual content type."""
    if not body:
        return "application/octet-stream"

    # PDF: %PDF-
    if body.startswith(b"%PDF-"):
        return "application/pdf"

    # JPEG: \xff\xd8\xff
    if body.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"

    # PNG: \x89PNG\r\n\x1a\n
    if body.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"

    # TIFF: II*\x00 (little-endian) or MM\x00* (big-endian)
    if body.startswith(b"II*\x00") or body.startswith(b"MM\x00*"):
        return "image/tiff"

    # GIF: GIF87a or GIF89a
    if body.startswith(b"GIF87a") or body.startswith(b"GIF89a"):
        return "image/gif"

    # ZIP: PK\x03\x04
    if body.startswith(b"PK\x03\x04"):
        return "application/zip"

    # XML: <?xml or <svg
    stripped = body[:1024].strip()
    if stripped.startswith(b"<?xml") or stripped.startswith(b"<svg"):
        return "application/xml"

    # JSON: starts with { or [ and parses cleanly
    if (stripped.startswith(b"{") and stripped.endswith(b"}")) or (
        stripped.startswith(b"[") and stripped.endswith(b"]")
    ):
        try:
            json.loads(body.decode("utf-8"))
            return "application/json"
        except (ValueError, UnicodeDecodeError):
            pass

    # Plain text: validate utf-8 decodability without null bytes
    if b"\x00" not in body[:1024]:
        try:
            body.decode("utf-8")
            return "text/plain"
        except UnicodeDecodeError:
            pass

    return "application/octet-stream"


def validate_upload_content(body: bytes) -> str:
    """Validate upload size and verify content type by inspecting magic bytes."""
    if len(body) > MAX_UPLOAD_SIZE:
        raise ValidationError(
            {"bodyBase64": [f"File size exceeds maximum allowed limit of {MAX_UPLOAD_SIZE} bytes."]}
        )

    mime_type = detect_mime_type(body)
    if mime_type not in ALLOWED_MIME_TYPES:
        allowed = ", ".join(sorted(ALLOWED_MIME_TYPES))
        raise ValidationError(
            {
                "bodyBase64": [
                    f"Content type '{mime_type}' is not permitted. Allowed types: {allowed}."
                ]
            }
        )

    return mime_type
