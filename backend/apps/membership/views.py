"""Membership API: public plans, plan management, requests and the approval queue."""

from __future__ import annotations

from typing import Any

from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import HasRole
from apps.accounts.throttling import UploadRateThrottle
from apps.audit.models import record_audit_event

from . import services
from .constants import MEMBERSHIP_APPROVER_ROLES, PLAN_MANAGER_ROLES
from .models import MembershipPlan, MembershipRequest
from .serializers import (
    CreateRequestSerializer,
    DocumentSerializer,
    MembershipRequestSerializer,
    PlanManageSerializer,
    PublicPlanSerializer,
    RecordPaymentSerializer,
    RejectSerializer,
    StaffMembershipRequestSerializer,
    SubscriptionSerializer,
)

# ---- Plans (ILMDAS-553) ----


class PublicPlanListView(APIView):
    """Active plans with prices, for guests choosing a membership."""

    authentication_classes: list = []
    permission_classes = [AllowAny]

    def get(self, request):
        plans = MembershipPlan.objects.filter(is_active=True)
        return Response(PublicPlanSerializer(plans, many=True).data)


class PlanManageViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """Staff create, edit and retire plans. Plans are retired, never deleted."""

    queryset = MembershipPlan.objects.all()
    serializer_class = PlanManageSerializer
    permission_classes = [IsAuthenticated, HasRole]
    required_roles = PLAN_MANAGER_ROLES

    def _audit(self, action: str, plan: MembershipPlan, **details: Any) -> None:
        record_audit_event(
            action=action,
            actor=self.request.user,
            object_type="MembershipPlan",
            object_id=str(plan.pk),
            details={"plan": plan.slug, **details},
            request=self.request,
        )

    def perform_create(self, serializer):
        plan = serializer.save()
        self._audit("membership.plan.created", plan, price=str(plan.price))

    def perform_update(self, serializer):
        was_active = serializer.instance.is_active
        plan = serializer.save()
        self._audit("membership.plan.updated", plan, price=str(plan.price))
        if was_active and not plan.is_active:
            self._audit("membership.plan.retired", plan)


# ---- A guest's own membership (ILMDAS-554) ----


class MyMembershipView(APIView):
    """The signed-in account's current subscription and its requests."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        subscription = services.current_subscription(request.user)
        requests = MembershipRequest.objects.filter(user=request.user).prefetch_related("documents")
        return Response(
            {
                "isMember": request.user.is_member,
                "subscription": SubscriptionSerializer(subscription).data if subscription else None,
                "requests": MembershipRequestSerializer(requests, many=True).data,
            }
        )


class MembershipRequestCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        membership_request = services.create_request(
            request.user, serializer.validated_data["plan"], request=request
        )
        return Response(
            MembershipRequestSerializer(membership_request).data,
            status=status.HTTP_201_CREATED,
        )


class MembershipDocumentUploadView(APIView):
    """Upload a supporting document to one's own open request (multipart field ``file``)."""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    throttle_classes = [UploadRateThrottle]

    def post(self, request, pk: int):
        # Another account's request is reported as missing, not forbidden.
        membership_request = get_object_or_404(MembershipRequest, pk=pk, user=request.user)
        uploaded = request.FILES.get("file")
        if uploaded is None:
            raise ValidationError({"file": ["Attach a file."]})
        document = services.upload_document(
            membership_request, uploaded, actor=request.user, request=request
        )
        return Response(DocumentSerializer(document).data, status=status.HTTP_201_CREATED)


# ---- Staff approval queue (ILMDAS-554) ----


class StaffRequestMixin:
    permission_classes = [IsAuthenticated, HasRole]
    required_roles = MEMBERSHIP_APPROVER_ROLES

    def get_request_or_404(self, pk: int) -> MembershipRequest:
        return get_object_or_404(MembershipRequest.objects.select_related("user", "plan"), pk=pk)


class MembershipRequestQueueView(StaffRequestMixin, APIView):
    """Requests for staff, filtered by ``?status=`` (default: awaiting approval)."""

    def get(self, request):
        wanted = request.query_params.get("status", MembershipRequest.Status.AWAITING_APPROVAL)
        if wanted not in MembershipRequest.Status.values:
            choices = ", ".join(MembershipRequest.Status.values)
            raise ValidationError({"status": [f"Use one of: {choices}."]})
        queue = (
            MembershipRequest.objects.filter(status=wanted)
            .select_related("user", "plan")
            .prefetch_related("documents")
            .order_by("created_at", "id")
        )
        return Response(StaffMembershipRequestSerializer(queue, many=True).data)


class RecordPaymentView(StaffRequestMixin, APIView):
    def post(self, request, pk: int):
        serializer = RecordPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = services.record_payment(
            self.get_request_or_404(pk),
            method=serializer.validated_data["method"],
            reference=serializer.validated_data["reference"],
            actor=request.user,
            request=request,
        )
        return Response(StaffMembershipRequestSerializer(updated).data)


class ApproveRequestView(StaffRequestMixin, APIView):
    def post(self, request, pk: int):
        approved, subscription = services.approve(
            self.get_request_or_404(pk), actor=request.user, request=request
        )
        body = StaffMembershipRequestSerializer(approved).data
        body["subscription"] = SubscriptionSerializer(subscription).data
        return Response(body)


class RejectRequestView(StaffRequestMixin, APIView):
    def post(self, request, pk: int):
        serializer = RejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rejected = services.reject(
            self.get_request_or_404(pk),
            actor=request.user,
            reason=serializer.validated_data["reason"],
            request=request,
        )
        return Response(StaffMembershipRequestSerializer(rejected).data)
