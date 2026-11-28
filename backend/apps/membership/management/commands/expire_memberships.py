"""End subscriptions whose period is over and remove the member role (ILMDAS-554).

Run daily, for example from cron: ``python manage.py expire_memberships``.
Safe to run repeatedly: already-expired subscriptions are skipped.
"""

from django.core.management.base import BaseCommand

from apps.membership.services import expire_memberships


class Command(BaseCommand):
    help = "Expire memberships whose period has ended and remove the member role."

    def handle(self, *args, **options):
        count = expire_memberships()
        self.stdout.write(f"Expired {count} membership(s).")
