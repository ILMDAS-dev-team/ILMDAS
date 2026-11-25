"""Custom user account and role models for ILMDAS (FR-SEC-002)."""

from __future__ import annotations

from django.conf import settings
from django.contrib.auth.hashers import identify_hasher
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class UserAccountStatus(models.TextChoices):
    """Lifecycle states for user accounts (FR-SEC-002)."""

    PENDING = "pending", "Pending"
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    SUSPENDED = "suspended", "Suspended"
    DEACTIVATED = "deactivated", "Deactivated"


class Role(models.TextChoices):
    MEMBER = "member", "Member"
    LIBRARY_STAFF = "staff", "Library Staff"
    ARCHIVIST = "archivist", "Archivist"
    ADMINISTRATOR = "administrator", "Administrator"


class User(AbstractUser):
    """User account entity adhering to FR-SEC-002 with secure one-way password hashing."""

    status = models.CharField(
        max_length=32,
        choices=UserAccountStatus.choices,
        default=UserAccountStatus.ACTIVE,
        db_index=True,
        help_text="Account lifecycle status (active, inactive, suspended, deactivated, pending).",
    )
    role = models.CharField(
        max_length=32,
        choices=Role.choices,
        default=Role.MEMBER,
        db_index=True,
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
        return self.role == Role.MEMBER

    @property
    def is_library_staff(self) -> bool:
        return self.role in (Role.LIBRARY_STAFF, Role.ADMINISTRATOR)

    @property
    def is_archivist(self) -> bool:
        return self.role in (Role.ARCHIVIST, Role.ADMINISTRATOR)

    @property
    def is_administrator(self) -> bool:
        return self.role == Role.ADMINISTRATOR or self.is_superuser

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
        """Ensure password is automatically hashed and is_active is synced with lifecycle status."""
        if self.password:
            try:
                identify_hasher(self.password)
            except ValueError:
                self.set_password(self.password)

        if self.status == UserAccountStatus.ACTIVE:
            self.is_active = True
        elif self.status in (
            UserAccountStatus.INACTIVE,
            UserAccountStatus.SUSPENDED,
            UserAccountStatus.DEACTIVATED,
            UserAccountStatus.PENDING,
        ):
            self.is_active = False

        super().save(*args, **kwargs)


UserAccount = User


class MembershipCategory(models.Model):
    """A staff-managed membership category (FR-MEM-004).

    No fee or loan-limit fields live here until those policies are approved.
    """

    code = models.SlugField(max_length=64, unique=True)
    name = models.CharField(max_length=128)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "membership category"
        verbose_name_plural = "membership categories"

    def __str__(self) -> str:
        state = "active" if self.is_active else "inactive"
        return f"{self.name} ({state})"


class Membership(models.Model):
    """The member record that links an account to a membership category."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="membership",
    )
    category = models.ForeignKey(
        MembershipCategory,
        on_delete=models.PROTECT,
        related_name="memberships",
    )
    joined_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-joined_at"]
        verbose_name = "membership"
        verbose_name_plural = "memberships"

    def __str__(self) -> str:
        return f"{self.user.get_username()} ({self.category.name})"
