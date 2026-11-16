"""Platform endpoints used by the scaffold. Feature workflows come later."""

from __future__ import annotations

import base64
import binascii

from django.db import connection
from django.http import Http404
from rest_framework.exceptions import NotAuthenticated, PermissionDenied, Throttled, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import CharField, Serializer
from rest_framework.views import APIView

from .exceptions import Conflict
from .iiif import IiifClient
from .models import ObjectReference
from .search import CatalogueIndex
from .storage import ObjectStorage, ObjectStorageError


class ProbeSerializer(Serializer):
    name = CharField()


def database_health() -> dict:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        return {"ok": False, "detail": "unreachable"}
    return {"ok": True, "detail": "reachable"}


def collect_health() -> dict:
    checks = {
        "database": database_health(),
        "elasticsearch": CatalogueIndex().health(),
        "objectStorage": ObjectStorage().health(),
    }
    status = "ok" if all(item["ok"] for item in checks.values()) else "failed"
    return {"status": status, "checks": checks}


class HealthView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]

    def get(self, request):
        payload = collect_health()
        status_code = 200 if payload["status"] == "ok" else 503
        return Response(payload, status=status_code)


class ValidationProbeView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ProbeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"name": serializer.validated_data["name"]})


class SessionProbeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"authenticated": True})


class ErrorProbeView(APIView):
    """Exercises the remaining error codes without a business workflow."""

    authentication_classes: list = []
    permission_classes = [AllowAny]

    def get(self, request):
        kind = request.query_params.get("kind", "")
        if kind == "authorization":
            raise PermissionDenied()
        if kind == "not_found":
            raise Http404()
        if kind == "conflict":
            raise Conflict()
        if kind == "rate_limit":
            raise Throttled(wait=1)
        if kind == "unavailable":
            raise RuntimeError("internal-detail-not-for-clients")
        if kind == "authentication":
            raise NotAuthenticated()
        raise ValidationError({"kind": ["Choose a documented error kind."]})


class ObjectUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        object_key = request.data.get("objectKey", "")
        encoded = request.data.get("bodyBase64", "")
        if not object_key or not encoded:
            raise ValidationError({"objectKey": ["objectKey and bodyBase64 are required."]})
        try:
            body = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValidationError({"bodyBase64": ["bodyBase64 is not valid base64."]}) from exc
        try:
            stored = ObjectStorage().put_private(object_key, body)
        except ObjectStorageError as exc:
            raise RuntimeError("object storage is unavailable") from exc
        record = ObjectReference.objects.create(
            object_key=stored.object_key,
            reference=stored.reference,
            checksum_sha256=stored.checksum_sha256,
        )
        return Response(
            {
                "id": record.id,
                "reference": record.reference,
                "checksumSha256": record.checksum_sha256,
            },
            status=201,
        )


class ObjectDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, object_id: int):
        try:
            record = ObjectReference.objects.get(pk=object_id)
        except ObjectReference.DoesNotExist as exc:
            raise Http404() from exc
        return Response(
            {
                "id": record.id,
                "reference": record.reference,
                "checksumSha256": record.checksum_sha256,
            }
        )


class IiifStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        status = IiifClient().configuration_status()
        http_status = 200 if status["status"] == "configured" else 503
        return Response(status, status=http_status)


class CatalogueIndexView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        CatalogueIndex().rebuild()
        return Response({"index": CatalogueIndex().index_name, "status": "rebuilt"}, status=201)

    def delete(self, request):
        CatalogueIndex().delete()
        return Response(status=204)
