"""Test settings. Values here are fixtures, not credentials."""

import os

os.environ["ILMDAS_SKIP_ENV_FILE"] = "1"
os.environ.setdefault("SECRET_KEY", "test-only-secret")
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", "sqlite:///test.sqlite3")
os.environ["ILMDAS_ENVIRONMENT"] = "test"
os.environ["S3_ENDPOINT_URL"] = os.environ.get("TEST_S3_ENDPOINT_URL", "")
os.environ["S3_BUCKET_NAME"] = os.environ.get("TEST_S3_BUCKET_NAME", "")
os.environ["ELASTICSEARCH_URL"] = os.environ.get("TEST_ELASTICSEARCH_URL", "")
os.environ["IIIF_ENDPOINT"] = os.environ.get("TEST_IIIF_ENDPOINT", "")

from .base import *  # noqa: E402,F403

DEBUG = False
ENVIRONMENT = "test"
DATABASES = {
    "default": dj_database_url.parse(
        os.environ.get("TEST_DATABASE_URL", "sqlite:///test.sqlite3"),
        conn_max_age=0,
    )
}
S3_ENDPOINT_URL = os.environ.get("TEST_S3_ENDPOINT_URL", "")
S3_BUCKET_NAME = os.environ.get("TEST_S3_BUCKET_NAME", "")
ELASTICSEARCH_URL = os.environ.get("TEST_ELASTICSEARCH_URL", "")
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_THROTTLE_RATES": {
        "anon": "1000/minute",
        "user": "1000/minute",
        "login": "1000/minute",
        "upload": "1000/minute",
    },
}
