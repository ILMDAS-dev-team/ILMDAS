"""Test helpers for accounts and roles."""

from __future__ import annotations

from .models import Role, User, UserRole, seed_roles

DEFAULT_TEST_PASSWORD = "Test@123456!"  # noqa: S105  # pragma: allowlist secret


def make_user(
    username: str, *role_codes: str, password: str = DEFAULT_TEST_PASSWORD, **extra
) -> User:
    """Create a user holding the given role codes (plus member, which every account gets)."""
    seed_roles()
    user = User.objects.create_user(username=username, password=password, **extra)
    for code in role_codes:
        UserRole.objects.get_or_create(user=user, role=Role.objects.get(code=code))
    return user
