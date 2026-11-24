"""Pytest fixtures."""

import os

os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.test"
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", "sqlite:///test.sqlite3")

import pytest  # noqa: E402
from django.core.cache import cache  # noqa: E402
from rest_framework.test import APIClient  # noqa: E402


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api_client():
    return APIClient()
