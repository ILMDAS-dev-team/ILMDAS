"""Test settings. Values here are fixtures, not credentials."""

import os

os.environ.setdefault("ILMDAS_SKIP_ENV_FILE", "1")
os.environ.setdefault("SECRET_KEY", "test-only-secret")
os.environ.setdefault("DATABASE_URL", "sqlite:///test.sqlite3")
os.environ.setdefault("ILMDAS_ENVIRONMENT", "test")

from .base import *  # noqa: E402,F403

DEBUG = False
ENVIRONMENT = "test"
