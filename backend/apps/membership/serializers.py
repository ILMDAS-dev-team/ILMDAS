"""Serializers for membership plans, requests and subscriptions (ILMDAS-553, 554)."""

from __future__ import annotations

from rest_framework import serializers

from .models import (
    MembershipDocument,
    MembershipPlan,
    MembershipRequest,
    MembershipSubscription,
)

PLAN_PUBLIC_FIELDS = [
    "id",
    "name",
    "slug",
    "description",
    "price",
    "currency",
    "price_display",
    "duration_months",
    "loan_limit",
    "restricted_archive_access",
    "benefits",
    "requires_documents",
]


class PublicPlanSerializer(serializers.ModelSerializer):
    """What guests see: active plans with their prices and benefits."""

    price_display = serializers.CharField(read_only=True)

    class Meta:
        model = MembershipPlan
        fields = PLAN_PUBLIC_FIELDS
        read_only_fields = PLAN_PUBLIC_FIELDS


class PlanManageSerializer(serializers.ModelSerializer):
    """Staff create, edit and retire plans."""

    price_display = serializers.CharField(read_only=True)

    class Meta:
        model = MembershipPlan
        fields = [*PLAN_PUBLIC_FIELDS, "is_active", "sort_order", "created_at", "updated_at"]
        read_only_fields = ["id", "price_display", "created_at", "updated_at"]


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipDocument
        fields = ["id", "original_name", "content_type", "size", "uploaded_at"]
        read_only_fields = fields


class MembershipRequestSerializer(serializers.ModelSerializer):
    """A request as its owner sees it."""

    plan = PublicPlanSerializer(read_only=True)
    documents = DocumentSerializer(many=True, read_only=True)

    class Meta:
        model = MembershipRequest
        fields = [
            "id",
            "plan",
            "status",
            "amount",
            "currency",
            "payment_method",
            "payment_reference",
            "paid_at",
            "rejection_reason",
            "decided_at",
            "documents",
            "created_at",
        ]
        read_only_fields = fields


class RequestApplicantSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()


class StaffMembershipRequestSerializer(MembershipRequestSerializer):
    """A request in the staff approval queue, with the applicant."""

    user = RequestApplicantSerializer(read_only=True)

    class Meta(MembershipRequestSerializer.Meta):
        fields = [*MembershipRequestSerializer.Meta.fields, "user"]
        read_only_fields = fields


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PublicPlanSerializer(read_only=True)

    class Meta:
        model = MembershipSubscription
        fields = ["id", "plan", "starts_at", "ends_at"]
        read_only_fields = fields


class CreateRequestSerializer(serializers.Serializer):
    plan = serializers.SlugRelatedField(slug_field="slug", queryset=MembershipPlan.objects.all())


class RecordPaymentSerializer(serializers.Serializer):
    method = serializers.ChoiceField(choices=MembershipRequest.PaymentMethod.choices)
    reference = serializers.CharField(max_length=128)


class RejectSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=2000)
