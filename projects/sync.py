"""Bring the database in line with the workspaces on disk.

Only descriptive fields come from disk. Status, lead, members, journal entries and runs
belong to the database and are never touched, so syncing is always safe to repeat.
"""
import logging
from dataclasses import dataclass, field

from django.conf import settings
from django.db import transaction

from learning.models import Module

from .manifests import discover
from .models import Experiment, Project

log = logging.getLogger("qml.projects")


@dataclass
class SyncReport:
    created: list = field(default_factory=list)
    updated: list = field(default_factory=list)
    errors: list = field(default_factory=list)      # ManifestError objects
    warnings: list = field(default_factory=list)    # strings

    @property
    def ok(self):
        return not self.errors


def sync_projects(root=None):
    manifests, errors = discover(root or settings.QML_PROJECTS_DIR)
    report = SyncReport(errors=list(errors))
    modules = {m.number: m for m in Module.objects.all()}
    for manifest in manifests:
        try:
            with transaction.atomic():
                _sync_one(manifest, modules, report)
        except Exception as exc:                 # keep syncing the other projects
            log.exception("Could not sync %s", manifest.slug)
            report.warnings.append(f"{manifest.slug}: not synced ({exc})")
    for error in report.errors:
        log.warning("Invalid workspace: %s", error)
    return report


def _sync_one(manifest, modules, report):
    project, created = Project.objects.update_or_create(
        slug=manifest.slug,
        defaults={
            "number": manifest.number, "title": manifest.title, "track": manifest.track,
            "difficulty": manifest.difficulty, "summary": manifest.summary, "tools": manifest.tools,
            "workspace": manifest.folder.name,
        },
    )
    (report.created if created else report.updated).append(manifest.slug)
    missing = [n for n in manifest.builds_on if n not in modules]
    if missing:
        report.warnings.append(f"{manifest.slug}: unknown module number(s) {missing}; run seed_portal first")
    project.builds_on.set([modules[n] for n in manifest.builds_on if n in modules])

    for order, exp in enumerate(manifest.experiments):
        Experiment.objects.update_or_create(
            project=project, slug=exp.slug,
            defaults={"title": exp.title, "description": exp.description, "script": exp.script,
                      "figure": exp.figure, "params": exp.params or {}, "order": order, "active": True},
        )
    project.experiments.exclude(slug__in=[e.slug for e in manifest.experiments]).update(active=False)
