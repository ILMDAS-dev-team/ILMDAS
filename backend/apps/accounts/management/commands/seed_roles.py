"""Seed the seven named ILMDAS roles into the database. Idempotent."""

from django.core.management.base import BaseCommand

from apps.accounts.models import seed_roles


class Command(BaseCommand):
    help = "Create the seven named ILMDAS roles if they do not already exist."

    def handle(self, *args, **options):
        seed_roles()
        self.stdout.write(self.style.SUCCESS("Roles seeded successfully."))
