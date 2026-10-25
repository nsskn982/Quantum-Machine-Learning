from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from projects.constants import DIFFICULTIES, TRACKS
from projects.models import Project
from projects.scaffold import create_workspace
from projects.sync import sync_projects

from .sync_projects import print_report


class Command(BaseCommand):
    help = ("Create a workspace in qml_projects/<slug>/ with a manifest, README and starter experiment. "
            "If a project with this slug was added on the website, its details are used.")

    def add_arguments(self, parser):
        parser.add_argument("slug")
        parser.add_argument("--title")
        parser.add_argument("--track", choices=list(TRACKS))
        parser.add_argument("--difficulty", choices=list(DIFFICULTIES))
        parser.add_argument("--summary")
        parser.add_argument("--tools", default="")
        parser.add_argument("--builds-on", nargs="*", type=int, default=None, help="Module numbers, e.g. 5 7")

    def handle(self, slug, **opts):
        existing = Project.objects.filter(slug=slug).first()
        values = {
            "title": opts["title"] or (existing and existing.title),
            "track": opts["track"] or (existing and existing.track),
            "difficulty": opts["difficulty"] or (existing and existing.difficulty),
            "summary": opts["summary"] or (existing and existing.summary),
            "tools": opts["tools"] or (existing.tools if existing else ""),
            "number": existing.number if existing else None,
            "builds_on": opts["builds_on"] if opts["builds_on"] is not None else (
                list(existing.builds_on.values_list("number", flat=True)) if existing else []),
        }
        missing = [k for k in ("title", "track", "difficulty", "summary") if not values[k]]
        if missing:
            raise CommandError(f"Missing --{' --'.join(missing)} (no project '{slug}' exists to copy them from).")
        try:
            folder = create_workspace(settings.QML_PROJECTS_DIR, slug, **values)
        except (ValueError, FileExistsError) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(f"Created {folder}"))
        print_report(self, sync_projects())
