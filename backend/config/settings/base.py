"""Settings shared by development, test, and production."""

from __future__ import annotations

import os
from pathlib import Path

import dj_database_url
from corsheaders.defaults import default_headers as default_cors_headers

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

AUTH_USER_MODEL = "accounts.User"

# SRS FR-SEC-002: bcrypt/Argon2. Argon2 hashes new and changed passwords. The rest are
# Django's default hashers, kept so every existing hash stays recognised: User.save()
# re-hashes any value it cannot identify, which would destroy an unlisted hash.
# Django re-hashes older hashes as Argon2 on the next successful login.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.ScryptPasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 12,
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

DATA_UPLOAD_MAX_MEMORY_SIZE = (
    20 * 1024 * 1024
)  # 20 MB ceiling to accommodate base64 payload overhead (SEC-09)

ELASTICSEARCH_URL = os.environ.get("ELASTICSEARCH_URL", "")
ELASTICSEARCH_INDEX = os.environ.get("ELASTICSEARCH_INDEX", "ilmdas-catalogue")
ELASTICSEARCH_API_KEY = os.environ.get("ELASTICSEARCH_API_KEY", "")
ELASTICSEARCH_CA_CERTS = os.environ.get("ELASTICSEARCH_CA_CERTS", "")
ELASTICSEARCH_VERIFY_CERTS = os.environ.get(
    "ELASTICSEARCH_VERIFY_CERTS", "true"
).strip().lower() in ("true", "1", "yes")

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
    "apps.accounts",
    "apps.audit",
    "apps.core",
    "apps.catalogue",
    "apps.circulation",
    "apps.archive",
    "apps.publishing",
    "apps.payments",
    "apps.membership",
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
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/day",
        "user": "1000/day",
        "login": "5/minute",
        "upload": "20/minute",
        "registration": "10/hour",
    },
}

# Registration and invite emails (ILMDAS-549). The provider is an open decision
# (ILMDAS-119): Django's email backend is the adapter, so a provider only needs settings.
# Development prints emails to the console; production defaults to SMTP.
# Blank values (as in .env.example) fall back to the defaults.
EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND") or "django.core.mail.backends.console.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST") or "localhost"
EMAIL_PORT = int(os.environ.get("EMAIL_PORT") or "25")
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = (os.environ.get("EMAIL_USE_TLS") or "false").strip().lower() in (
    "true",
    "1",
    "yes",
)
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL") or "ILMDAS <no-reply@localhost>"
# Links in emails point at the Next.js frontend.
FRONTEND_BASE_URL = (os.environ.get("FRONTEND_BASE_URL") or "http://localhost:3010").rstrip("/")
# Invite and email-verification links expire after this many seconds (3 days).
PASSWORD_RESET_TIMEOUT = int(os.environ.get("ACCOUNT_LINK_TIMEOUT_SECONDS") or str(3 * 24 * 3600))

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:3010").split(",")
    if origin.strip()
]
# The frontend (another origin in development) sends the session cookie and the
# CSRF token, so credentialed CORS requests must be allowed for these origins.
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = (*default_cors_headers, "x-correlation-id")
# Django checks the Origin header of unsafe requests against this list.
CSRF_TRUSTED_ORIGINS = list(CORS_ALLOWED_ORIGINS)
