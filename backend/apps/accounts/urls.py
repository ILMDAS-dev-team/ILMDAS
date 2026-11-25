"""Account and authentication URL patterns."""

from django.urls import path

from .views import CsrfCookieView, LoginView, LogoutView, SessionView

urlpatterns = [
    path("csrf/", CsrfCookieView.as_view(), name="auth-csrf"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("me/", SessionView.as_view(), name="auth-me"),
]
