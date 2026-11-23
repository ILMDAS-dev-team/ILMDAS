"""Private object-storage client. Binaries stay out of database columns."""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from django.conf import settings

logger = logging.getLogger("ilmdas.storage")


class ObjectStorageError(RuntimeError):
    pass


class ObjectStorageConflictError(ObjectStorageError):
    pass


@dataclass(frozen=True)
class StoredObject:
    reference: str
    checksum_sha256: str
    object_key: str


class ObjectStorage:
    def __init__(self, client=None, bucket: str | None = None):
        self.client = client
        self.bucket = settings.S3_BUCKET_NAME if bucket is None else bucket

    def _client(self):
        if self.client is not None:
            return self.client
        if not settings.S3_ENDPOINT_URL or not self.bucket:
            raise ObjectStorageError("Object storage is not configured")
        return boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
            region_name=settings.S3_REGION,
            config=Config(signature_version="s3v4"),
        )

    def exists(self, object_key: str) -> bool:
        if not object_key:
            return False
        client = self._client()
        if not hasattr(client, "head_object"):
            return False
        try:
            client.head_object(Bucket=self.bucket, Key=object_key)
            return True
        except ClientError as exc:
            code = str(exc.response.get("Error", {}).get("Code", ""))
            if code in ("404", "NoSuchKey", "NotFound"):
                return False
            logger.error("S3 head_object failed unexpectedly for key %s: %s", object_key, exc)
            raise ObjectStorageError(f"Storage existence check failed: {exc}") from exc
        except Exception as exc:
            if isinstance(exc, ObjectStorageError):
                raise
            logger.error("Unexpected error checking storage key %s: %s", object_key, exc)
            raise ObjectStorageError(f"Storage existence check failed: {exc}") from exc

    def delete(self, object_key: str) -> None:
        if not object_key:
            return
        try:
            client = self._client()
        except ObjectStorageError as exc:
            logger.warning("Could not obtain S3 client to delete %s: %s", object_key, exc)
            return
        if hasattr(client, "delete_object"):
            try:
                client.delete_object(Bucket=self.bucket, Key=object_key)
            except Exception as exc:
                logger.warning(
                    "Failed to delete storage object '%s' during cleanup: %s",
                    object_key,
                    exc,
                )

    def put_private(
        self, object_key: str, body: bytes, content_type: str = "application/octet-stream"
    ) -> StoredObject:
        if self.exists(object_key):
            raise ObjectStorageConflictError(
                f"Object with key '{object_key}' already exists in storage."
            )
        checksum = hashlib.sha256(body).hexdigest()
        self._client().put_object(
            Bucket=self.bucket,
            Key=object_key,
            Body=body,
            ContentType=content_type,
            ACL="private",
        )
        return StoredObject(
            reference=f"s3://{self.bucket}/{object_key}",
            checksum_sha256=checksum,
            object_key=object_key,
        )

    def health(self) -> dict:
        if not settings.S3_ENDPOINT_URL or not self.bucket:
            return {"ok": False, "detail": "not configured"}
        try:
            self._client().head_bucket(Bucket=self.bucket)
        except Exception:
            return {"ok": False, "detail": "unreachable"}
        return {"ok": True, "detail": "reachable"}
