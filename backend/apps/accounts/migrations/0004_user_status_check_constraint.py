"""Add database check constraint for User.status lifecycle values."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_move_user_role_to_userrole"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="user",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    status__in=["pending", "active", "inactive", "suspended", "deactivated"]
                ),
                name="accounts_user_status_valid",
            ),
        ),
    ]
