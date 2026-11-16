"""Settings shared by development, test, and production."""

from __future__ import annotations

import os
from pathlib import Path

import dj_database_url

from .env import load_env_file, require_env

load_env_file()
_required = require_env("SECRET_KEY", "DATABASE_URL")

BASE_DIR = Path(__file__).resolve().parents[2]

SECRET_KEY = _required["SECRET_KEY"]
DATABASES = {"default": dj_database_url.parse(_required["DATABASE_URL"], conn_max_age=60)}

DEBUG = False
ENVIRONMENT = os.environ.get("ILMDAS_ENVIRONMENT", "development")
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

LANGUAGE_CODE = "en"
TIME_ZONE = "Africa/Addis_Ababa"
USE_I18N = True
USE_TZ = True

ELASTICSEARCH_URL = os.environ.get("ELASTICSEARCH_URL", "")
ELASTICSEARCH_INDEX = os.environ.get("ELASTICSEARCH_INDEX", "ilmdas-catalogue")
S3_ENDPOINT_URL = os.environ.get("S3_ENDPOINT_URL", "")
S3_ACCESS_KEY_ID = os.environ.get("S3_ACCESS_KEY_ID", "")
S3_SECRET_ACCESS_KEY = os.environ.get("S3_SECRET_ACCESS_KEY", "")
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "")
S3_REGION = os.environ.get("S3_REGION", "us-east-1")
IIIF_ENDPOINT = os.environ.get("IIIF_ENDPOINT", "")
IIIF_FIXTURE_IDENTIFIER = os.environ.get("IIIF_FIXTURE_IDENTIFIER", "fixture-image")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "apps.core",
    "apps.accounts",
    "apps.catalogue",
    "apps.circulation",
    "apps.archive",
    "apps.publishing",
    "apps.payments",
    "apps.audit",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.CorrelationIdMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "apps.core.exceptions.api_exception_handler",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:3010").split(",")
    if origin.strip()
]
