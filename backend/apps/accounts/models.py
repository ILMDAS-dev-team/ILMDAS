"""Custom user and role models for ILMDAS."""

from __future__ import annotations

from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    MEMBER = "member", "Member"
    LIBRARY_STAFF = "staff", "Library Staff"
    ARCHIVIST = "archivist", "Archivist"
    ADMINISTRATOR = "administrator", "Administrator"


class User(AbstractUser):
    role = models.CharField(
        max_length=32,
        choices=Role.choices,
        default=Role.MEMBER,
        db_index=True,
    )

    class Meta:
        ordering = ["username"]

    def __str__(self) -> str:
        return f"{self.username} ({self.get_role_display()})"

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
