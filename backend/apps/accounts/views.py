"""Views for authentication and user profiles."""

from __future__ import annotations

from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.models import record_audit_event

from .serializers import LoginSerializer, UserProfileSerializer
from .throttling import LoginRateThrottle


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
            raise AuthenticationFailed("Authentication failed.")

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
