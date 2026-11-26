"""Read-only audit review API for system administrators (ILMDAS-31)."""

from __future__ import annotations

from datetime import date, datetime, time

from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated

from apps.accounts.constants import ROLE_SYSTEM_ADMINISTRATOR
from apps.accounts.permissions import HasRole

from .models import AuditRecord
from .serializers import AuditRecordSerializer


class AuditPagination(PageNumberPagination):
    page_size = 50
    max_page_size = 200
    page_size_query_param = "page_size"


class _AuditReadOnly:
    """GET only: generic read views reject PUT/PATCH/DELETE with 405."""

    permission_classes = [IsAuthenticated, HasRole]
    # Until the role matrix (ILMDAS-124) is approved, only the system administrator reviews.
    required_role = ROLE_SYSTEM_ADMINISTRATOR
    serializer_class = AuditRecordSerializer


def _parse_date(value: str, field: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError({field: "Use the date format YYYY-MM-DD."}) from exc


class AuditEventListView(_AuditReadOnly, ListAPIView):
    pagination_class = AuditPagination

    def get_queryset(self):
        params = self.request.query_params
        events = AuditRecord.objects.all().order_by("-timestamp", "-id")
        if actor := params.get("actor", "").strip():
            events = events.filter(actor_username__icontains=actor)
        if action := params.get("action", "").strip():
            # "auth." matches every auth event; "auth.login" matches exactly that action.
            events = (
                events.filter(action__startswith=action)
                if action.endswith(".")
                else events.filter(action=action)
            )
        tz = timezone.get_current_timezone()
        if date_from := params.get("date_from", "").strip():
            start = datetime.combine(_parse_date(date_from, "date_from"), time.min, tz)
            events = events.filter(timestamp__gte=start)
        if date_to := params.get("date_to", "").strip():
            end = datetime.combine(_parse_date(date_to, "date_to"), time.max, tz)
            events = events.filter(timestamp__lte=end)
        return events


class AuditEventDetailView(_AuditReadOnly, RetrieveAPIView):
    queryset = AuditRecord.objects.all()
