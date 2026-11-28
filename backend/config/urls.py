"""ILMDAS URL configuration."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.core.urls")),
    path("api/v1/", include("apps.accounts.rbac_urls")),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/audit/", include("apps.audit.urls")),
    path("api/v1/membership/", include("apps.membership.urls")),
    path("api/v1/", include("apps.homepage.urls")),
]
