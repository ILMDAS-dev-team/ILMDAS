"""Platform endpoints used by the scaffold. Feature workflows come later."""

from __future__ import annotations

import base64
import binascii
import logging
import re
import uuid

from django.conf import settings
from django.db import IntegrityError, connection, transaction
from django.http import Http404
from django.utils import timezone
from rest_framework.exceptions import NotAuthenticated, PermissionDenied, Throttled, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import CharField, Serializer
from rest_framework.views import APIView

from apps.accounts.constants import ROLE_DIGITAL_ARCHIVIST, ROLE_SYSTEM_ADMINISTRATOR
from apps.accounts.permissions import HasRole
from apps.accounts.serializers import UserSummarySerializer
from apps.accounts.throttling import UploadRateThrottle
from apps.audit.models import record_audit_event

from .content_type import ALLOWED_MIME_TYPES, MAX_UPLOAD_SIZE, validate_upload_content
from .exceptions import Conflict, ServiceUnavailable
from .iiif import IiifClient
from .models import ObjectReference
from .permissions import CanUploadArchiveObject, CanViewObjectDetail
from .scanner import MalwareScanStatus, scan_object
from .search import CatalogueIndex
from .storage import ObjectStorage, ObjectStorageConflictError, ObjectStorageError

logger = logging.getLogger("ilmdas.storage")

SAFE_PREFIX_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")
SAFE_KEY_PATTERN = re.compile(r"^[a-zA-Z0-9_\-\./]+$")

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_BASE64_LENGTH = ((4 * MAX_UPLOAD_BYTES // 3) + 3) & ~3


def generate_object_key(prefix: str = "archive") -> str:
    """Generate a server-side object key with date prefix and UUID."""
    if not isinstance(prefix, str) or not SAFE_PREFIX_PATTERN.match(prefix):
        prefix = "archive"
    date_path = timezone.now().strftime("%Y/%m/%d")
    return f"{prefix}/{date_path}/{uuid.uuid4().hex}"


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
    permission_classes = [AllowAny]

    def get(self, request):
        payload = collect_health()
        status_code = 200 if payload["status"] == "ok" else 503
        if request.user and request.user.is_authenticated:
            return Response(payload, status=status_code)
        return Response({"status": payload["status"]}, status=status_code)


class ValidationProbeView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]

    def dispatch(self, request, *args, **kwargs):
        if getattr(settings, "ENVIRONMENT", "") == "production":
            raise Http404()
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        serializer = ProbeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"name": serializer.validated_data["name"]})


class SessionProbeView(APIView):
    permission_classes = [IsAuthenticated]

    def dispatch(self, request, *args, **kwargs):
        if getattr(settings, "ENVIRONMENT", "") == "production":
            raise Http404()
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        serializer = UserSummarySerializer(request.user)
        return Response({"authenticated": True, "user": serializer.data})


class ErrorProbeView(APIView):
    """Exercises the remaining error codes without a business workflow."""

    authentication_classes: list = []
    permission_classes = [AllowAny]

    def dispatch(self, request, *args, **kwargs):
        if getattr(settings, "ENVIRONMENT", "") == "production":
            raise Http404()
        return super().dispatch(request, *args, **kwargs)

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
    permission_classes = [IsAuthenticated, HasRole]
    required_roles = [ROLE_SYSTEM_ADMINISTRATOR, ROLE_DIGITAL_ARCHIVIST]
    throttle_classes = [UploadRateThrottle]

    def post(self, request):
        encoded = request.data.get("bodyBase64", "")
        if not isinstance(encoded, str) or not encoded.strip():
            raise ValidationError({"bodyBase64": ["bodyBase64 is required."]})
        if len(encoded) > MAX_BASE64_LENGTH:
            raise ValidationError(
                {
                    "bodyBase64": [
                        f"Payload exceeds maximum allowed limit of {MAX_UPLOAD_BYTES // (1024 * 1024)}MB."
                    ]
                }
            )
        try:
            body = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValidationError({"bodyBase64": ["bodyBase64 is not valid base64."]}) from exc

        # SEC-09: Validate content by magic bytes and enforce size limits
        content_type = validate_upload_content(body)

        # SEC-09: Malware scanning hook
        scan_result = scan_object(body)
        if scan_result["status"] == MalwareScanStatus.INFECTED:
            raise ValidationError({"bodyBase64": [f"Malware detected: {scan_result['detail']}"]})

        object_key = request.data.get("objectKey", "")
        if isinstance(object_key, str):
            object_key = object_key.strip()
        if object_key:
            if (
                ".." in object_key
                or object_key.startswith("/")
                or not SAFE_KEY_PATTERN.match(object_key)
            ):
                raise ValidationError(
                    {
                        "objectKey": [
                            "Invalid objectKey. Path traversal characters ('..') and leading slashes are forbidden."
                        ]
                    }
                )
        else:
            raw_prefix = request.data.get("prefix", "archive")
            prefix = raw_prefix if isinstance(raw_prefix, str) else "archive"
            object_key = generate_object_key(prefix)

        # SEC-01: Check for existing key in database and storage before writing
        storage = ObjectStorage()
        if ObjectReference.objects.filter(object_key=object_key).exists() or storage.exists(
            object_key
        ):
            raise Conflict(f"Object with key '{object_key}' already exists.")

        try:
            stored = storage.put_private(object_key, body, content_type=content_type)
        except ObjectStorageConflictError as exc:
            raise Conflict(str(exc)) from exc
        except ObjectStorageError as exc:
            logger.error("Object storage failure during upload: %s", exc)
            raise ServiceUnavailable("Object storage is unavailable.") from exc

        try:
            with transaction.atomic():
                record = ObjectReference.objects.create(
                    object_key=stored.object_key,
                    reference=stored.reference,
                    checksum_sha256=stored.checksum_sha256,
                    content_type=content_type,
                    scan_status=scan_result["status"],
                )
        except IntegrityError as exc:
            storage.delete(stored.object_key)
            raise Conflict(f"Object with key '{stored.object_key}' already exists.") from exc

        # SEC-17: Record audit event for sensitive archive upload
        record_audit_event(
            action="storage.upload",
            actor=request.user,
            object_type="ObjectReference",
            object_id=str(record.id),
            details={
                "object_key": record.object_key,
                "checksum": record.checksum_sha256,
                "content_type": record.content_type,
                "scan_status": record.scan_status,
            },
            request=request,
        )

        return Response(
            {
                "id": record.id,
                "objectKey": record.object_key,
                "reference": record.reference,
                "checksumSha256": record.checksum_sha256,
                "contentType": record.content_type,
                "scanStatus": record.scan_status,
            },
            status=201,
        )


class PresignedUploadView(APIView):
    permission_classes = [CanUploadArchiveObject]
    throttle_classes = [UploadRateThrottle]

    def post(self, request):
        filename = request.data.get("filename", "")
        content_type = request.data.get("contentType", "application/octet-stream")
        content_length = request.data.get("contentLength", 0)

        if content_length > MAX_UPLOAD_SIZE:
            raise ValidationError(
                {
                    "contentLength": [
                        f"Requested size exceeds maximum limit of {MAX_UPLOAD_SIZE} bytes."
                    ]
                }
            )
        if content_type not in ALLOWED_MIME_TYPES:
            raise ValidationError(
                {"contentType": [f"Content type '{content_type}' is not permitted."]}
            )

        object_key = generate_object_key("archive")
        storage = ObjectStorage()
        presigned = storage.generate_presigned_upload(
            object_key=object_key,
            content_type=content_type,
            max_size=MAX_UPLOAD_SIZE,
        )
        record_audit_event(
            action="storage.presign",
            actor=request.user,
            object_type="PresignedUpload",
            object_id=object_key,
            details={
                "content_type": content_type,
                "max_size": MAX_UPLOAD_SIZE,
                "filename": filename,
            },
            request=request,
        )
        return Response(presigned, status=200)


class ObjectDetailView(APIView):
    permission_classes = [CanViewObjectDetail]

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
                "contentType": record.content_type,
                "scanStatus": record.scan_status,
            }
        )


class IiifStatusView(APIView):
    permission_classes = [CanViewObjectDetail]

    def get(self, request):
        status = IiifClient().configuration_status()
        http_status = 200 if status["status"] == "configured" else 503
        return Response(status, status=http_status)


class CatalogueIndexView(APIView):
    permission_classes = [IsAuthenticated, HasRole]
    required_role = ROLE_SYSTEM_ADMINISTRATOR

    def post(self, request):
        CatalogueIndex().rebuild()
        record_audit_event(
            action="search.index.rebuild",
            actor=request.user,
            object_type="CatalogueIndex",
            object_id=CatalogueIndex().index_name,
            request=request,
        )
        return Response({"index": CatalogueIndex().index_name, "status": "rebuilt"}, status=201)

    def delete(self, request):
        CatalogueIndex().delete()
        record_audit_event(
            action="search.index.delete",
            actor=request.user,
            object_type="CatalogueIndex",
            object_id=CatalogueIndex().index_name,
            request=request,
        )
        return Response(status=204)
