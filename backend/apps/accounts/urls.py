"""Accounts URL routes: RBAC roles and authentication."""

from django.urls import path

from .views import (
    CsrfCookieView,
    CurrentUserRolesView,
    LoginView,
    LogoutView,
    RoleListView,
    SessionView,
    UserListView,
    UserRoleAssignView,
    UserRoleRemoveView,
)

urlpatterns = [
    # RBAC endpoints (ILMDAS-204, ILMDAS-205)
    path("roles/", RoleListView.as_view(), name="role-list"),
    path("users/", UserListView.as_view(), name="user-list"),
    path("users/me/roles/", CurrentUserRolesView.as_view(), name="current-user-roles"),
    path(
        "users/<int:user_id>/roles/",
        UserRoleAssignView.as_view(),
        name="user-role-assign",
    ),
    path(
        "users/<int:user_id>/roles/<str:role_code>/",
        UserRoleRemoveView.as_view(),
        name="user-role-remove",
    ),
    # Authentication endpoints (ILMDAS-27)
    path("csrf/", CsrfCookieView.as_view(), name="auth-csrf"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("me/", SessionView.as_view(), name="auth-me"),
]
