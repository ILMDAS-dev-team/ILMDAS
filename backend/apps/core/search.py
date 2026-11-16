"""Rebuildable catalogue index. The database remains the authority."""

from __future__ import annotations

from django.conf import settings
from elasticsearch import Elasticsearch


class SearchNotConfigured(RuntimeError):
    pass


class CatalogueIndex:
    def __init__(self, client=None, index_name: str | None = None):
        self.client = client
        self.index_name = index_name or settings.ELASTICSEARCH_INDEX

    def _client(self):
        if self.client is not None:
            return self.client
        if not settings.ELASTICSEARCH_URL:
            raise SearchNotConfigured("Elasticsearch is not configured")
        return Elasticsearch(settings.ELASTICSEARCH_URL, request_timeout=2)

    def _guard_non_production(self) -> None:
        if getattr(settings, "ENVIRONMENT", "development") == "production":
            raise PermissionError(
                "Catalogue index rebuild is limited to non-production environments"
            )

    def rebuild(self) -> None:
        self._guard_non_production()
        client = self._client()
        if client.indices.exists(index=self.index_name):
            client.indices.delete(index=self.index_name)
        client.indices.create(
            index=self.index_name,
            settings={"number_of_shards": 1, "number_of_replicas": 0},
            mappings={"properties": {"title": {"type": "text"}}},
        )

    def delete(self) -> None:
        self._guard_non_production()
        self._client().indices.delete(index=self.index_name)

    def health(self) -> dict:
        if not settings.ELASTICSEARCH_URL and self.client is None:
            return {"ok": False, "detail": "not configured"}
        try:
            client = self._client()
            if hasattr(client, "ping") and not client.ping():
                return {"ok": False, "detail": "unreachable"}
        except Exception:
            return {"ok": False, "detail": "unreachable"}
        return {"ok": True, "detail": "reachable"}
