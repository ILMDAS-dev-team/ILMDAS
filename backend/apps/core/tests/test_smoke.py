"""Live-stack smoke checks. Skipped by default (see pyproject addopts)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

import pytest

SMOKE_BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://localhost:8010").rstrip("/")


@pytest.mark.smoke
def test_live_health_endpoint():
    """Compose stack must be up: GET /api/v1/health/ returns status ok."""
    url = f"{SMOKE_BASE_URL}/api/v1/health/"
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            status_code = response.getcode()
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        pytest.fail(f"health unreachable at {url}: {exc}")

    assert status_code == 200
    assert body.get("status") == "ok"
