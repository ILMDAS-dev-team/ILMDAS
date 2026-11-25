"""Accounts API views: role listing, user-role assignment, current-user roles, and authentication."""

from __future__ import annotations

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.constants import ROLE_SYSTEM_ADMINISTRATOR
from apps.accounts.models import Role, UserRole
from apps.accounts.permissions import HasRole
from apps.accounts.serializers import (
    AssignRoleSerializer,
    LoginSerializer,
    RoleSerializer,
    UserProfileSerializer,
    UserSummarySerializer,
)
from apps.audit.models import record_audit_event
from apps.core.exceptions import InvalidCredentials

from .throttling import LoginRateThrottle

User = get_user_model()


# RBAC Views (ILMDAS-204, ILMDAS-205)


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

        # Audit trail for role assignment
        record_audit_event(
            action="role.assigned",
            actor=request.user,
            object_type="UserRole",
            object_id=str(target_user.id),
            details={
                "target_user": target_user.username,
                "role_code": role_code,
                "role_name": role.name,
            },
            request=request,
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

        # Audit trail for role revocation
        record_audit_event(
            action="role.revoked",
            actor=request.user,
            object_type="UserRole",
            object_id=str(target_user.id),
            details={
                "target_user": target_user.username,
                "role_code": role_code,
                "role_name": role.name,
            },
            request=request,
        )

        return Response(
            {"detail": f"Role '{role_code}' removed from user '{target_user.username}'."},
            status=status.HTTP_200_OK,
        )


# Authentication Views


class CsrfCookieView(APIView):
    """Issue a CSRF cookie for browser clients before login."""

    authentication_classes: list = []
    permission_classes = [AllowAny]

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        return Response({"csrfToken": get_token(request)})


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        # DRF only checks CSRF for already-authenticated sessions, so an anonymous
        # login POST would skip it. Enforce it here (403 through the shared error contract).
        SessionAuthentication().enforce_csrf(request)

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]

        user = authenticate(request, username=username, password=password)
        if user is None:
            record_audit_event(
                action="auth.login.failed",
                actor=username,
                object_type="user",
                object_id=username,
                request=request,
            )
            raise InvalidCredentials()

        login(request, user)
        record_audit_event(
            action="auth.login",
            actor=user,
            object_type="user",
            object_id=str(user.id),
            request=request,
        )
        data = UserProfileSerializer(user).data
        data["authenticated"] = True
        return Response(data)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        record_audit_event(
            action="auth.logout",
            actor=request.user,
            object_type="user",
            object_id=str(request.user.id),
            request=request,
        )
        logout(request)
        return Response({"status": "logged_out", "authenticated": False})


class SessionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = UserProfileSerializer(request.user).data
        data["authenticated"] = True
        return Response(data)
