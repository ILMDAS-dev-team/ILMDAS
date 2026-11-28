"""Serializers for accounts: RBAC roles and authentication."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.accounts.constants import STAFF_ROLE_CODES
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


def role_list(user) -> list[dict[str, str]]:
    """The user's roles as [{code, name}], the shape the frontend's AuthUser.roles expects."""
    return [
        {"code": ur.role.code, "name": ur.role.name}
        for ur in user.user_roles.select_related("role").all()
    ]


class UserSummarySerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "roles"]

    def get_roles(self, obj):
        return role_list(obj)


# Authentication Serializers (custom User model)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class UserProfileSerializer(serializers.ModelSerializer):
    isStaff = serializers.BooleanField(source="is_library_staff", read_only=True)
    isAdministrator = serializers.BooleanField(source="is_administrator", read_only=True)
    isArchivist = serializers.BooleanField(source="is_archivist", read_only=True)
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "status",
            "roles",
            "created_at",
            "last_login",
            "isStaff",
            "isAdministrator",
            "isArchivist",
        ]

    def get_roles(self, obj):
        return role_list(obj)


# Registration Serializers (ILMDAS-551, ILMDAS-552)

# One message for a taken username or email, so the API does not say which one exists.
DUPLICATE_ACCOUNT_MESSAGE = (
    "An account cannot be created with these details. "
    "If you already have an account, sign in instead."
)


def account_details_taken(username: str, email: str) -> bool:
    return (
        User.objects.filter(username__iexact=username).exists()
        or User.objects.filter(email__iexact=email).exists()
    )


def check_password_strength(password: str, **user_fields: str) -> None:
    """Run the configured password validators, comparing against the account details."""
    try:
        validate_password(password, user=User(**user_fields))
    except DjangoValidationError as exc:
        raise serializers.ValidationError({"password": list(exc.messages)}) from exc


class StaffAccountCreateSerializer(serializers.Serializer):
    """A system administrator registers a staff account (ILMDAS-551)."""

    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    roles = serializers.ListField(
        child=serializers.ChoiceField(choices=STAFF_ROLE_CODES),
        allow_empty=False,
    )

    def validate(self, attrs):
        if account_details_taken(attrs["username"], attrs["email"]):
            raise serializers.ValidationError(DUPLICATE_ACCOUNT_MESSAGE)
        attrs["roles"] = list(dict.fromkeys(attrs["roles"]))  # drop repeats, keep order
        return attrs


class RegistrationSerializer(serializers.Serializer):
    """Public self-registration (ILMDAS-552)."""

    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    accept_terms = serializers.BooleanField()

    def validate_accept_terms(self, value: bool) -> bool:
        if not value:
            raise serializers.ValidationError("You must accept the terms to register.")
        return value

    def validate(self, attrs):
        if account_details_taken(attrs["username"], attrs["email"]):
            raise serializers.ValidationError(DUPLICATE_ACCOUNT_MESSAGE)
        check_password_strength(
            attrs["password"],
            username=attrs["username"],
            email=attrs["email"],
            first_name=attrs["first_name"],
            last_name=attrs.get("last_name", ""),
        )
        return attrs


class AccountLinkSerializer(serializers.Serializer):
    """The uid and token from an emailed link."""

    uid = serializers.CharField()
    token = serializers.CharField()


class AcceptInviteSerializer(AccountLinkSerializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
