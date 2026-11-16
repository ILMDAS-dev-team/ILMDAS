"""Request correlation identifier."""

from __future__ import annotations

import uuid


class CorrelationIdMiddleware:
    header = "X-Correlation-ID"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        incoming = request.headers.get(self.header, "").strip()
        correlation_id = incoming or str(uuid.uuid4())
        request.correlation_id = correlation_id
        response = self.get_response(request)
        response[self.header] = correlation_id
        return response
