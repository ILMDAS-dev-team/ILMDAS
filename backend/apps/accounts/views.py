"""Views for authentication and user profiles."""

from __future__ import annotations

from django.contrib.auth import authenticate, login, logout
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.models import record_audit_event

from .serializers import LoginSerializer, UserProfileSerializer
from .throttling import LoginRateThrottle


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

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
            raise AuthenticationFailed("Invalid username or password.")

        login(request, user)
        record_audit_event(
            action="auth.login",
            actor=user,
            object_type="user",
            object_id=str(user.id),
            request=request,
        )
        return Response(UserProfileSerializer(user).data)


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
        return Response({"status": "logged_out"})


class SessionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserProfileSerializer(request.user).data)
