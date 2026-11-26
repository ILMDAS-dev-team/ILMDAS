"""Migration 0003 moves the legacy User.role value into UserRole (ILMDAS-28 follow-up)."""

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

BEFORE = [("accounts", "0002_seed_roles")]
AFTER = [("accounts", "0003_move_user_role_to_userrole")]


@pytest.mark.django_db(transaction=True)
def test_legacy_roles_are_copied_to_userrole():
    executor = MigrationExecutor(connection)
    executor.migrate(BEFORE)
    old_apps = executor.loader.project_state(BEFORE).apps
    OldUser = old_apps.get_model("accounts", "User")
    for username, legacy in [
        ("m", "member"),
        ("s", "staff"),
        ("a", "archivist"),
        ("adm", "administrator"),
    ]:
        OldUser.objects.create(username=username, role=legacy)

    executor = MigrationExecutor(connection)
    executor.loader.build_graph()
    executor.migrate(AFTER)
    new_apps = executor.loader.project_state(AFTER).apps
    UserRole = new_apps.get_model("accounts", "UserRole")

    def codes(username):
        return set(
            UserRole.objects.filter(user__username=username).values_list("role__code", flat=True)
        )

    assert codes("m") == {"member"}
    assert codes("s") == {"member", "librarian"}
    assert codes("a") == {"member", "digital_archivist"}
    assert codes("adm") == {"member", "system_administrator"}
