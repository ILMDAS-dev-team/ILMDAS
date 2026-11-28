"""Accounts API views: role listing, user-role assignment, current-user roles, and authentication."""

from __future__ import annotations

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.db import transaction
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
from apps.accounts.emails import send_email_verification, send_staff_invite
from apps.accounts.models import Role, UserAccountStatus, UserRole
from apps.accounts.permissions import HasRole
from apps.accounts.serializers import (
    AcceptInviteSerializer,
    AccountLinkSerializer,
    AssignRoleSerializer,
    LoginSerializer,
    RegistrationSerializer,
    ResendVerificationSerializer,
    RoleSerializer,
    StaffAccountCreateSerializer,
    UserProfileSerializer,
    UserSummarySerializer,
    check_password_strength,
)
from apps.accounts.tokens import (
    email_verification_tokens,
    pending_user_from_link,
    staff_invite_tokens,
)
from apps.audit.models import AuditOutcome, record_audit_event
from apps.core.exceptions import Conflict, InvalidCredentials

from .throttling import LoginRateThrottle, RegistrationRateThrottle

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
        assignment = UserRole.objects.filter(user=target_user, role=role)

        if assignment.exists():
            # SRS: every active account holds one or more roles.
            if not target_user.user_roles.exclude(role=role).exists():
                raise Conflict("A user must keep at least one role.")
            if role.code == ROLE_SYSTEM_ADMINISTRATOR:
                # Keep someone able to manage roles: no self-removal, no removing the last admin.
                if target_user.pk == request.user.pk:
                    raise Conflict("You cannot remove your own administrator role.")
                if not UserRole.objects.filter(role=role).exclude(user=target_user).exists():
                    raise Conflict("At least one system administrator must remain.")

        deleted, _ = assignment.delete()
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
                outcome=AuditOutcome.FAILURE,
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


# Registration Views (ILMDAS-551, ILMDAS-552)


class AnonymousCsrfMixin:
    """Enforce CSRF on anonymous POSTs, as LoginView does (DRF skips it otherwise)."""

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)  # type: ignore[misc]
        SessionAuthentication().enforce_csrf(request)


class StaffAccountCreateView(APIView):
    """A system administrator registers a staff account and invites the person (ILMDAS-551).

    The account starts pending with no usable password. The invite link lets the
    staff member set their own password, so the administrator never handles it.
    """

    permission_classes = [IsAuthenticated, HasRole]
    required_role = ROLE_SYSTEM_ADMINISTRATOR

    def post(self, request):
        serializer = StaffAccountCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        with transaction.atomic():
            user = User.objects.create_user(
                username=data["username"],
                email=data["email"],
                password=None,  # unusable until the invite is accepted
                first_name=data.get("first_name", ""),
                last_name=data.get("last_name", ""),
                status=UserAccountStatus.PENDING,
            )
            roles = list(Role.objects.filter(code__in=data["roles"]))
            for role in roles:
                UserRole.objects.get_or_create(
                    user=user, role=role, defaults={"assigned_by": request.user}
                )
            record_audit_event(
                action="account.staff.created",
                actor=request.user,
                object_type="user",
                object_id=str(user.id),
                details={"target_user": user.username, "roles": data["roles"]},
                request=request,
            )
            for role in roles:
                record_audit_event(
                    action="role.assigned",
                    actor=request.user,
                    object_type="UserRole",
                    object_id=str(user.id),
                    details={
                        "target_user": user.username,
                        "role_code": role.code,
                        "role_name": role.name,
                        "via": "staff_registration",
                    },
                    request=request,
                )
        send_staff_invite(user)

        body = UserSummarySerializer(user).data
        body["status"] = user.status
        return Response(body, status=status.HTTP_201_CREATED)


class AcceptInviteView(AnonymousCsrfMixin, APIView):
    """A new staff member sets their password from the invite link (ILMDAS-551)."""

    authentication_classes: list = []
    permission_classes = [AllowAny]
    throttle_classes = [RegistrationRateThrottle]

    def post(self, request):
        serializer = AcceptInviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = pending_user_from_link(
            serializer.validated_data["uid"],
            serializer.validated_data["token"],
            staff_invite_tokens,
        )
        password = serializer.validated_data["password"]
        check_password_strength(
            password,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
        )
        user.set_password(password)
        user.status = UserAccountStatus.ACTIVE
        user.save()
        record_audit_event(
            action="account.invite.accepted",
            actor=user,
            object_type="user",
            object_id=str(user.id),
            request=request,
        )
        return Response({"detail": "Your password is set. You can now sign in."})


class RegisterView(AnonymousCsrfMixin, APIView):
    """Public self-registration (ILMDAS-552).

    The account is pending, and cannot sign in, until the email address is verified.
    It then becomes an active guest.
    """

    authentication_classes: list = []
    permission_classes = [AllowAny]
    throttle_classes = [RegistrationRateThrottle]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = User.objects.create_user(
            username=data["username"],
            email=data["email"],
            password=data["password"],
            first_name=data["first_name"],
            last_name=data.get("last_name", ""),
            status=UserAccountStatus.PENDING,
        )
        record_audit_event(
            action="account.registered",
            actor=user,
            object_type="user",
            object_id=str(user.id),
            request=request,
        )
        send_email_verification(user)
        return Response(
            {
                "detail": "Check your email for a link to activate your account.",
                "status": user.status,
            },
            status=status.HTTP_201_CREATED,
        )


class VerifyEmailView(AnonymousCsrfMixin, APIView):
    """Activate a self-registered account from the emailed link (ILMDAS-552)."""

    authentication_classes: list = []
    permission_classes = [AllowAny]
    throttle_classes = [RegistrationRateThrottle]

    def post(self, request):
        serializer = AccountLinkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = pending_user_from_link(
            serializer.validated_data["uid"],
            serializer.validated_data["token"],
            email_verification_tokens,
        )
        user.status = UserAccountStatus.ACTIVE
        user.save()
        record_audit_event(
            action="account.email_verified",
            actor=user,
            object_type="user",
            object_id=str(user.id),
            request=request,
        )
        return Response({"detail": "Your email is verified. You can now sign in."})


class ResendVerificationView(AnonymousCsrfMixin, APIView):
    """Send a new verification link. Always answers the same way (ILMDAS-552)."""

    authentication_classes: list = []
    permission_classes = [AllowAny]
    throttle_classes = [RegistrationRateThrottle]

    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = (
            User.objects.filter(
                email__iexact=serializer.validated_data["email"],
                status=UserAccountStatus.PENDING,
            )
            .order_by("id")
            .first()
        )
        # Staff invites have no usable password; they are resent by an administrator.
        if user is not None and user.has_usable_password():
            send_email_verification(user)
        return Response(
            {"detail": "If a pending account uses this email, a new link has been sent."}
        )
