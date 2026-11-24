"""Accounts URL routes."""

from django.urls import path

from .views import (
    CurrentUserRolesView,
    RoleListView,
    UserListView,
    UserRoleAssignView,
    UserRoleRemoveView,
)

urlpatterns = [
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
]
