"""Audit review routes (ILMDAS-31), served under /api/v1/audit/."""

from django.urls import path

from .views import AuditEventDetailView, AuditEventListView

urlpatterns = [
    path("events/", AuditEventListView.as_view(), name="audit-event-list"),
    path("events/<int:pk>/", AuditEventDetailView.as_view(), name="audit-event-detail"),
]
