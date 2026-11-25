"""Serializers for accounts and authentication."""

from rest_framework import serializers

from .models import Membership, User
from .services import evaluate_member_eligibility, get_membership_for


class UserProfileSerializer(serializers.ModelSerializer):
    isStaff = serializers.BooleanField(source="is_library_staff", read_only=True)
    isAdministrator = serializers.BooleanField(source="is_administrator", read_only=True)
    isArchivist = serializers.BooleanField(source="is_archivist", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "status",
            "role",
            "created_at",
            "last_login",
            "isStaff",
            "isAdministrator",
            "isArchivist",
        ]


class StaffMemberSerializer(serializers.ModelSerializer):
    """Staff-only member record with a plain-language borrowing explanation."""

    membership = serializers.SerializerMethodField()
    borrowingEligibility = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "status",
            "role",
            "membership",
            "borrowingEligibility",
        ]

    def get_membership(self, obj: User) -> dict | None:
        membership = get_membership_for(obj)
        if membership is None:
            return None
        return self._serialize_membership(membership)

    def get_borrowingEligibility(self, obj: User) -> dict:
        return evaluate_member_eligibility(obj).as_dict()

    @staticmethod
    def _serialize_membership(membership: Membership) -> dict:
        return {
            "id": membership.id,
            "category": {
                "id": membership.category.id,
                "code": membership.category.code,
                "name": membership.category.name,
                "isActive": membership.category.is_active,
            },
            "joinedAt": membership.joined_at,
        }


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
