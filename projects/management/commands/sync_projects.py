from django.core.management.base import BaseCommand, CommandError

from projects.sync import sync_projects


def print_report(command, report):
    style = command.style
    command.stdout.write(style.SUCCESS(f"Projects: {len(report.created)} created, {len(report.updated)} updated"))
    for warning in report.warnings:
        command.stdout.write(style.WARNING(f"  warning: {warning}"))
    for error in report.errors:
        command.stdout.write(style.ERROR(f"  invalid: {error.path}"))
        for problem in error.problems:
            command.stdout.write(style.ERROR(f"    - {problem}"))


class Command(BaseCommand):
    help = "Read qml_projects/*/project.toml into the database. Keeps status, members and journals."

    def add_arguments(self, parser):
        parser.add_argument("--strict", action="store_true", help="Exit with an error if any workspace is invalid")

    def handle(self, *args, strict=False, **options):
        report = sync_projects()
        print_report(self, report)
        if strict and not report.ok:
            raise CommandError(f"{len(report.errors)} invalid workspace(s)")
