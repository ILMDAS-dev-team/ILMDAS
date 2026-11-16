"""IIIF / Cantaloupe client. A missing endpoint is not treated as success."""

from __future__ import annotations

import json
from urllib.request import urlopen

from django.conf import settings


def _default_get(url: str) -> dict:
    with urlopen(url, timeout=3) as response:
        return json.loads(response.read().decode("utf-8"))


class IiifClient:
    def __init__(self, endpoint: str | None = None, http_get=None):
        self.endpoint = settings.IIIF_ENDPOINT if endpoint is None else endpoint
        self.http_get = http_get or _default_get

    def configuration_status(self) -> dict:
        if not self.endpoint:
            return {
                "status": "not_configured",
                "message": "IIIF endpoint is not configured",
            }
        return {
            "status": "configured",
            "message": "IIIF endpoint is configured",
        }

    def image_info(self, identifier: str) -> dict:
        if not self.endpoint:
            return {
                "status": "not_configured",
                "message": "IIIF endpoint is not configured",
            }
        url = f"{self.endpoint.rstrip('/')}/{identifier}/info.json"
        return {
            "status": "ok",
            "identifier": identifier,
            "info": self.http_get(url),
        }
