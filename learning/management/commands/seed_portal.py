from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from learning.content import MODULES
from learning.models import Module
from projects.management.commands.sync_projects import print_report
from projects.sync import sync_projects


class Command(BaseCommand):
    help = "Load the 8 modules, then sync project workspaces. Safe to run again."

    def add_arguments(self, parser):
        parser.add_argument("--strict", action="store_true", help="Exit with an error if any workspace is invalid")

    def handle(self, *args, strict=False, **options):
        with transaction.atomic():
            for data in MODULES:
                Module.objects.update_or_create(number=data["number"], defaults=data)
        self.stdout.write(self.style.SUCCESS(f"Modules: {len(MODULES)} ready"))
        report = sync_projects()
        print_report(self, report)
        if strict and not report.ok:
            raise CommandError(f"{len(report.errors)} invalid workspace(s)")
