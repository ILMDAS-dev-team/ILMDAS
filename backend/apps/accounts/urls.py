"""Authentication routes (ILMDAS-27) and registration (ILMDAS-549), under /api/v1/auth/."""

from django.urls import path

from .views import (
    AcceptInviteView,
    CsrfCookieView,
    LoginView,
    LogoutView,
    RegisterView,
    ResendVerificationView,
    SessionView,
    VerifyEmailView,
)

urlpatterns = [
    path("csrf/", CsrfCookieView.as_view(), name="auth-csrf"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("me/", SessionView.as_view(), name="auth-me"),
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("verify-email/", VerifyEmailView.as_view(), name="auth-verify-email"),
    path(
        "verify-email/resend/",
        ResendVerificationView.as_view(),
        name="auth-verify-email-resend",
    ),
    path("invite/accept/", AcceptInviteView.as_view(), name="auth-invite-accept"),
]
