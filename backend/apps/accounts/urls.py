"""Accounts URL routes: RBAC roles and authentication."""

from django.urls import path

from .views import (
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
    # Authentication endpoints
    path("login/", LoginView.as_view(), name="auth-login"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("session/", SessionView.as_view(), name="auth-session"),
]