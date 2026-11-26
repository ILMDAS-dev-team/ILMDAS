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


ROLES_MIGRATION = [("accounts", "0002_create_role_userrole")]
INITIAL = [("accounts", "0001_initial")]


def _tables():
    return set(connection.introspection.table_names())


@pytest.mark.django_db(transaction=True)
def test_database_from_main_gets_role_tables_on_upgrade():
    """A database migrated from main has 0001 without the role tables; upgrading creates them."""
    executor = MigrationExecutor(connection)
    executor.migrate(INITIAL)
    assert "accounts_role" not in _tables()

    executor = MigrationExecutor(connection)
    executor.loader.build_graph()
    executor.migrate(ROLES_MIGRATION)
    assert {"accounts_role", "accounts_userrole"} <= _tables()


@pytest.mark.django_db(transaction=True)
def test_database_from_develop_with_existing_tables_upgrades_cleanly():
    """A database whose old 0001 already created the tables must not fail on CREATE TABLE."""
    executor = MigrationExecutor(connection)
    executor.migrate(INITIAL)
    roles_state = executor.loader.project_state(ROLES_MIGRATION).apps
    with connection.schema_editor() as editor:
        editor.create_model(roles_state.get_model("accounts", "Role"))
        editor.create_model(roles_state.get_model("accounts", "UserRole"))

    executor = MigrationExecutor(connection)
    executor.loader.build_graph()
    executor.migrate(ROLES_MIGRATION)
    assert {"accounts_role", "accounts_userrole"} <= _tables()
