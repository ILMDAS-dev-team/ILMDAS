"""Accounts API views: role listing, user-role assignment, current-user roles."""

from __future__ import annotations

from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.constants import ROLE_SYSTEM_ADMINISTRATOR
from apps.accounts.models import Role, UserRole
from apps.accounts.permissions import HasRole
from apps.accounts.serializers import (
    AssignRoleSerializer,
    RoleSerializer,
    UserSummarySerializer,
)


class RoleListView(APIView):
    """List all available roles. System Administrator only."""

    permission_classes = [IsAuthenticated, HasRole]
    required_role = ROLE_SYSTEM_ADMINISTRATOR

    def get(self, request):
        roles = Role.objects.all().order_by("name")
        serializer = RoleSerializer(roles, many=True)
        return Response(serializer.data)


class UserListView(APIView):
    """List all users with their assigned roles. System Administrator only."""

    permission_classes = [IsAuthenticated, HasRole]
    required_role = ROLE_SYSTEM_ADMINISTRATOR

    def get(self, request):
        users = User.objects.all().order_by("username")
        serializer = UserSummarySerializer(users, many=True)
        return Response(serializer.data)


class CurrentUserRolesView(APIView):
    """Return the authenticated user's own roles."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSummarySerializer(request.user)
        return Response(serializer.data)


class UserRoleAssignView(APIView):
    """Assign a role to a user. System Administrator only."""

    permission_classes = [IsAuthenticated, HasRole]
    required_role = ROLE_SYSTEM_ADMINISTRATOR

    def post(self, request, user_id):
        target_user = get_object_or_404(User, pk=user_id)
        serializer = AssignRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        role_code = serializer.validated_data["role_code"]
        role = get_object_or_404(Role, code=role_code)

        _, created = UserRole.objects.get_or_create(
            user=target_user,
            role=role,
            defaults={"assigned_by": request.user},
        )
        if not created:
            return Response(
                {"detail": f"User already has role '{role_code}'."},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            {"detail": f"Role '{role_code}' assigned to user '{target_user.username}'."},
            status=status.HTTP_201_CREATED,
        )


class UserRoleRemoveView(APIView):
    """Remove a role from a user. System Administrator only."""

    permission_classes = [IsAuthenticated, HasRole]
    required_role = ROLE_SYSTEM_ADMINISTRATOR

    def delete(self, request, user_id, role_code):
        target_user = get_object_or_404(User, pk=user_id)
        role = get_object_or_404(Role, code=role_code)

        deleted, _ = UserRole.objects.filter(user=target_user, role=role).delete()
        if not deleted:
            return Response(
                {"detail": f"User does not have role '{role_code}'."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {"detail": f"Role '{role_code}' removed from user '{target_user.username}'."},
            status=status.HTTP_200_OK,
        )
