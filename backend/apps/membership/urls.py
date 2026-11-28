"""Membership routes (ILMDAS-553, ILMDAS-554), served under /api/v1/membership/."""

from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import (
    ApproveRequestView,
    MembershipDocumentUploadView,
    MembershipRequestCreateView,
    MembershipRequestQueueView,
    MyMembershipView,
    PlanManageViewSet,
    PublicPlanListView,
    RecordPaymentView,
    RejectRequestView,
)

router = SimpleRouter()
router.register("manage/plans", PlanManageViewSet, basename="membership-plan-manage")

urlpatterns = [
    path("plans/", PublicPlanListView.as_view(), name="membership-plans"),
    path("me/", MyMembershipView.as_view(), name="membership-me"),
    path("requests/", MembershipRequestCreateView.as_view(), name="membership-request-create"),
    path(
        "requests/<int:pk>/documents/",
        MembershipDocumentUploadView.as_view(),
        name="membership-request-documents",
    ),
    path(
        "manage/requests/",
        MembershipRequestQueueView.as_view(),
        name="membership-request-queue",
    ),
    path(
        "manage/requests/<int:pk>/payment/",
        RecordPaymentView.as_view(),
        name="membership-request-payment",
    ),
    path(
        "manage/requests/<int:pk>/approve/",
        ApproveRequestView.as_view(),
        name="membership-request-approve",
    ),
    path(
        "manage/requests/<int:pk>/reject/",
        RejectRequestView.as_view(),
        name="membership-request-reject",
    ),
    *router.urls,
]
