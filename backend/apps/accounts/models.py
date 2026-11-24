"""Accounts models: roles and user-role assignments."""

from __future__ import annotations

from django.contrib.auth.models import User
from django.db import models

from .constants import ALL_ROLE_CODES, ROLE_DESCRIPTIONS, ROLE_NAMES


class Role(models.Model):
    """Named system role with a stable code identifier."""

    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        app_label = "accounts"

    def __str__(self) -> str:
        return self.name


class UserRole(models.Model):
    """Assignment of a role to a user. A user may hold multiple roles."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_roles")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="user_roles")
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_user_roles",
    )

    class Meta:
        unique_together = [("user", "role")]
        ordering = ["-assigned_at"]
        app_label = "accounts"

    def __str__(self) -> str:
        return f"{self.user.username} -> {self.role.name}"


def seed_roles() -> None:
    """Create the seven named ILMDAS roles if they do not already exist.

    Idempotent: re-running creates no duplicates.
    """
    for code in ALL_ROLE_CODES:
        Role.objects.get_or_create(
            code=code,
            defaults={
                "name": ROLE_NAMES[code],
                "description": ROLE_DESCRIPTIONS[code],
            },
        )
