"""Serializers for accounts: RBAC roles and authentication."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.accounts.models import Role, UserRole

User = get_user_model()


# RBAC Role Serializers (ILMDAS-204, ILMDAS-205)


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "name", "code", "description", "created_at"]
        read_only_fields = ["id", "created_at"]


class UserRoleSerializer(serializers.ModelSerializer):
    role_code = serializers.SlugRelatedField(
        slug_field="code",
        queryset=Role.objects.all(),
        source="role",
        write_only=True,
    )
    role = RoleSerializer(read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = UserRole
        fields = ["id", "username", "role", "role_code", "assigned_at", "assigned_by"]
        read_only_fields = ["id", "role", "assigned_at", "assigned_by"]


class AssignRoleSerializer(serializers.Serializer):
    role_code = serializers.SlugField(max_length=50)

    def validate_role_code(self, value):
        if not Role.objects.filter(code=value).exists():
            raise serializers.ValidationError(f"Role with code '{value}' does not exist.")
        return value


class UserSummarySerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "roles"]

    def get_roles(self, obj):
        return [
            {"code": ur.role.code, "name": ur.role.name}
            for ur in obj.user_roles.select_related("role").all()
        ]


# Authentication Serializers (custom User model)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


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
