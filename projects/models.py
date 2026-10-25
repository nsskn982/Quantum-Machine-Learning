from django.conf import settings
from django.db import models
from django.urls import reverse

from core.exceptions import ScriptUnavailable
from core.scripts import ScriptSpec, safe_script_path

from .constants import DIFFICULTIES, SLUG, TRACKS


class Project(models.Model):
    """An open-ended QML project. Code and plan live in qml_projects/<workspace>/; people and
    progress live here. There is no 'done': projects stay open for the next question."""

    class Status(models.TextChoices):
        OPEN = "open", "Looking for people"
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        ARCHIVED = "archived", "Archived"

    number = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Position in the plan's list")
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=120)
    track = models.CharField(max_length=20, choices=list(TRACKS.items()))
    difficulty = models.CharField(max_length=10, choices=list(DIFFICULTIES.items()))
    summary = models.TextField()
    tools = models.CharField(max_length=120, blank=True)
    builds_on = models.ManyToManyField("learning.Module", blank=True, related_name="projects")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    lead = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                             related_name="led_qml_projects")
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="qml_projects")
    repo_url = models.URLField(blank=True)
    workspace = models.CharField(max_length=80, blank=True, help_text="Folder name under qml_projects/")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = [models.F("number").asc(nulls_last=True), "title"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("project_detail", args=[self.slug])

    def is_member(self, user):
        return user.is_authenticated and self.members.filter(pk=user.pk).exists()

    def workspace_path(self):
        """Absolute workspace folder, or None if not set, invalid or missing."""
        if not self.workspace or not SLUG.match(self.workspace):
            return None
        root = settings.QML_PROJECTS_DIR.resolve()
        path = (root / self.workspace).resolve()
        return path if path.parent == root and path.is_dir() else None

    def readme(self):
        path = self.workspace_path()
        if path and (path / "README.md").is_file():
            try:
                return (path / "README.md").read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                return ""
        return ""


class Experiment(models.Model):
    """A runnable script inside a project workspace, declared in project.toml."""

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="experiments")
    slug = models.SlugField()
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    script = models.CharField(max_length=200, help_text="Path inside the workspace, e.g. experiments/e01_baseline.py")
    figure = models.CharField(max_length=120, blank=True)
    params = models.JSONField(default=dict, blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    active = models.BooleanField(default=True, help_text="False once removed from project.toml (runs are kept)")

    class Meta:
        ordering = ["order", "slug"]
        constraints = [models.UniqueConstraint(fields=["project", "slug"], name="unique_experiment_per_project")]

    def __str__(self):
        return f"{self.project.slug}/{self.slug}"

    def get_absolute_url(self):
        return f"{self.project.get_absolute_url()}#exp-{self.slug}"

    def script_spec(self):
        workspace = self.project.workspace_path()
        if workspace is None:
            raise ScriptUnavailable(f"Project '{self.project.slug}' has no workspace folder on this server.")
        return ScriptSpec(
            label=str(self),
            path=safe_script_path(workspace, self.script),
            cwd=workspace,
            figure=self.figure,
            params=dict(self.params or {}),
            pythonpath=(settings.QML_LAB_DIR.resolve(), workspace),
        )

    def source_code(self):
        try:
            return self.script_spec().path.read_text(encoding="utf-8")
        except (ScriptUnavailable, OSError, UnicodeDecodeError):
            return ""


class Entry(models.Model):
    """One line in a project's research journal."""

    class Kind(models.TextChoices):
        NOTE = "note", "Note"
        RESULT = "result", "Result"
        DECISION = "decision", "Decision"
        QUESTION = "question", "Open question"
        NEXT_STEP = "next_step", "Next step"

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="entries")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.NOTE)
    text = models.TextField()
    run = models.ForeignKey("core.Run", null=True, blank=True, on_delete=models.SET_NULL, related_name="entries")
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]
        verbose_name_plural = "entries"

    def __str__(self):
        return f"{self.get_kind_display()}: {self.text[:60]}"
