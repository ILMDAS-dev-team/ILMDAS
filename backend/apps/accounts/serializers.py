"""Serializers for accounts and authentication."""

from rest_framework import serializers

from .models import User


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


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
