"""Public homepage API and role-guarded content management endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import HasRole
from apps.audit.models import record_audit_event

from .constants import WEBSITE_CONTENT_ROLES
from .models import (
    ContentCard,
    ContentSection,
    FeaturedResource,
    FooterLink,
    Homepage,
    InstitutionalUpdate,
    PopularSearch,
    ResourceCategory,
)
from .serializers import (
    ContentCardSerializer,
    ContentSectionSerializer,
    FeaturedResourceSerializer,
    FooterLinkSerializer,
    HomepageSerializer,
    InstitutionalUpdateSerializer,
    PopularSearchSerializer,
    ResourceCategorySerializer,
)
from .services import build_homepage_payload
from .translation import resolve_language

if TYPE_CHECKING:
    from rest_framework.request import Request


class HomepageView(APIView):
    """Anonymous public read of approved homepage content only."""

    authentication_classes: list = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(build_homepage_payload(resolve_language(request)))


class WebsiteContentMixin:
    """Only approved institutional users may create, edit or remove content."""

    request: Request

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated, HasRole]
    required_roles = WEBSITE_CONTENT_ROLES

    def save_kwargs(self) -> dict[str, Any]:
        return {}

    def _audit(self, action: str, instance: Any) -> None:
        record_audit_event(
            action=f"website.content.{action}",
            actor=self.request.user,
            object_type=type(instance).__name__,
            object_id=str(instance.pk),
            details={"title": getattr(instance, "title", "")},
            request=self.request,
        )

    def perform_create(self, serializer):
        instance = serializer.save(**self.save_kwargs())
        self._audit("create", instance)

    def perform_update(self, serializer):
        instance = serializer.save(**self.save_kwargs())
        self._audit("update", instance)

    def perform_destroy(self, instance):
        self._audit("delete", instance)
        instance.delete()


class HomepageManageViewSet(WebsiteContentMixin, viewsets.ModelViewSet):
    queryset = Homepage.objects.all()
    serializer_class = HomepageSerializer

    def save_kwargs(self) -> dict[str, Any]:
        return {"updated_by": self.request.user}


class PopularSearchViewSet(WebsiteContentMixin, viewsets.ModelViewSet):
    queryset = PopularSearch.objects.all()
    serializer_class = PopularSearchSerializer


class ResourceCategoryViewSet(WebsiteContentMixin, viewsets.ModelViewSet):
    queryset = ResourceCategory.objects.all()
    serializer_class = ResourceCategorySerializer


class ContentSectionViewSet(WebsiteContentMixin, viewsets.ModelViewSet):
    queryset = ContentSection.objects.all()
    serializer_class = ContentSectionSerializer


class ContentCardViewSet(WebsiteContentMixin, viewsets.ModelViewSet):
    queryset = ContentCard.objects.all()
    serializer_class = ContentCardSerializer


class FeaturedResourceViewSet(WebsiteContentMixin, viewsets.ModelViewSet):
    queryset = FeaturedResource.objects.all()
    serializer_class = FeaturedResourceSerializer


class InstitutionalUpdateViewSet(WebsiteContentMixin, viewsets.ModelViewSet):
    queryset = InstitutionalUpdate.objects.all()
    serializer_class = InstitutionalUpdateSerializer


class FooterLinkViewSet(WebsiteContentMixin, viewsets.ModelViewSet):
    queryset = FooterLink.objects.all()
    serializer_class = FooterLinkSerializer
