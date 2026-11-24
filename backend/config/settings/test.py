"""Test settings. Values here are fixtures, not credentials."""

import os

os.environ["ILMDAS_SKIP_ENV_FILE"] = "1"
os.environ.setdefault("SECRET_KEY", "test-only-secret")
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", "sqlite:///test.sqlite3")
os.environ["ILMDAS_ENVIRONMENT"] = "test"

from .base import *  # noqa: E402,F403

DEBUG = False
ENVIRONMENT = "test"
DATABASES = {
    "default": dj_database_url.parse(
        os.environ.get("TEST_DATABASE_URL", "sqlite:///test.sqlite3"),
        conn_max_age=0,
    )
}
