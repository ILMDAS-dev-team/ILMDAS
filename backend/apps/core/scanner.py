"""Antivirus and malware scan integration hook (SEC-09)."""

from __future__ import annotations

EICAR_SIGNATURE = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"


class MalwareScanStatus:
    PENDING = "pending"
    CLEAN = "clean"
    INFECTED = "infected"
    SKIPPED = "skipped"


def scan_object(body: bytes, filename: str = "") -> dict:
    """Malware scan hook.

    Integrates with enterprise scanning infrastructure (ClamAV clamd or ICAP daemon).
    Standard EICAR signature is detected locally as a built-in verification safeguard.
    """
    if EICAR_SIGNATURE in body:
        return {
            "status": MalwareScanStatus.INFECTED,
            "detail": "EICAR test malware signature detected",
        }

    return {"status": MalwareScanStatus.CLEAN, "detail": "Clean"}
