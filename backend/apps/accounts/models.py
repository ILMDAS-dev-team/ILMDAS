"""Accounts models: roles and user-role assignments."""

from __future__ import annotations

from django.conf import settings
from django.contrib.auth.hashers import UNUSABLE_PASSWORD_PREFIX, identify_hasher
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

from .constants import (
    ALL_ROLE_CODES,
    ROLE_DESCRIPTIONS,
    ROLE_DIGITAL_ARCHIVIST,
    ROLE_GUEST,
    ROLE_LIBRARIAN,
    ROLE_MEMBER,
    ROLE_NAMES,
    ROLE_SYSTEM_ADMINISTRATOR,
)


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

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_roles",
    )
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="user_roles")
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
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
    """Create the named ILMDAS roles if they do not already exist.

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


class UserAccountStatus(models.TextChoices):
    """Lifecycle states for user accounts (FR-SEC-002)."""

    PENDING = "pending", "Pending"
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    SUSPENDED = "suspended", "Suspended"
    DEACTIVATED = "deactivated", "Deactivated"


class User(AbstractUser):
    """User account entity adhering to FR-SEC-002 with secure one-way password hashing."""

    status = models.CharField(
        max_length=32,
        choices=UserAccountStatus.choices,
        default=UserAccountStatus.ACTIVE,
        db_index=True,
        help_text="Account lifecycle status (active, inactive, suspended, deactivated, pending).",
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="Timestamp when the user account was created.",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when the user account was last modified.",
    )

    class Meta:
        ordering = ["username"]
        verbose_name = "user account"
        verbose_name_plural = "user accounts"
        constraints = [
            models.CheckConstraint(
                condition=Q(status__in=UserAccountStatus.values),
                name="accounts_user_status_valid",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.username} ({self.get_status_display()})"

    @property
    def created_time(self):
        """Alias for created_at per FR-SEC-002 specification."""
        return self.created_at

    @property
    def last_login_time(self):
        """Alias for last_login per FR-SEC-002 specification."""
        return self.last_login

    @property
    def password_hash(self) -> str:
        """Expose the stored one-way hash string (never plain text)."""
        return self.password

    @property
    def is_member(self) -> bool:
        return self.has_any_role(ROLE_MEMBER)

    @property
    def is_guest(self) -> bool:
        """A registered account with no member role (ILMDAS-550)."""
        return not self.is_member

    @property
    def is_library_staff(self) -> bool:
        return self.has_any_role(ROLE_LIBRARIAN, ROLE_SYSTEM_ADMINISTRATOR)

    @property
    def is_archivist(self) -> bool:
        return self.has_any_role(ROLE_DIGITAL_ARCHIVIST, ROLE_SYSTEM_ADMINISTRATOR)

    @property
    def is_administrator(self) -> bool:
        return self.is_superuser or self.has_any_role(ROLE_SYSTEM_ADMINISTRATOR)

    def has_any_role(self, *codes: str) -> bool:
        """True if the user holds at least one of the given role codes (UserRole table)."""
        if not self.pk:
            return False
        return self.user_roles.filter(role__code__in=codes).exists()

    def activate(self) -> None:
        """Activate the user account."""
        self.status = UserAccountStatus.ACTIVE
        self.is_active = True
        self.save(update_fields=["status", "is_active", "updated_at"])

    def deactivate(self) -> None:
        """Deactivate the user account."""
        self.status = UserAccountStatus.INACTIVE
        self.is_active = False
        self.save(update_fields=["status", "is_active", "updated_at"])

    def suspend(self) -> None:
        """Suspend the user account."""
        self.status = UserAccountStatus.SUSPENDED
        self.is_active = False
        self.save(update_fields=["status", "is_active", "updated_at"])

    def save(self, *args, **kwargs) -> None:
        """Ensure password is automatically hashed, status is restricted to lifecycle values, and is_active is synced."""
        if self.status not in UserAccountStatus.values:
            raise ValidationError(
                f"Invalid account status '{self.status}'. Must be one of: {list(UserAccountStatus.values)}."
            )

        if self.password and not self.password.startswith(UNUSABLE_PASSWORD_PREFIX):
            try:
                identify_hasher(self.password)
            except ValueError:
                self.set_password(self.password)
                update_fields = kwargs.get("update_fields")
                if update_fields is not None:
                    kwargs["update_fields"] = set(update_fields) | {"password"}

        if self.status == UserAccountStatus.ACTIVE:
            self.is_active = True
        elif self.status in (
            UserAccountStatus.INACTIVE,
            UserAccountStatus.SUSPENDED,
            UserAccountStatus.DEACTIVATED,
            UserAccountStatus.PENDING,
        ):
            self.is_active = False

        is_new = self._state.adding
        super().save(*args, **kwargs)

        if is_new:
            # Every new account starts as a guest (ILMDAS-550). Staff roles are added on
            # top, and the member role comes only from an approved membership (ILMDAS-554).
            guest = Role.objects.filter(code=ROLE_GUEST).first()
            if guest is not None:
                UserRole.objects.get_or_create(user=self, role=guest)


UserAccount = User
