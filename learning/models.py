import re

from django.conf import settings
from django.db import models
from django.urls import reverse

from core.exceptions import ScriptUnavailable
from core.scripts import ScriptSpec, safe_script_path

MODULE_SCRIPT = re.compile(r"^m\d{2}_[a-z0-9_]+\.py$")


class Module(models.Model):
    """One learning module from the QML plan (Module 1 to 8)."""

    number = models.PositiveSmallIntegerField(unique=True)
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=120)
    week = models.CharField(max_length=20, help_text="e.g. '5-6'")
    tool = models.CharField(max_length=80, help_text="Main framework used")
    summary = models.CharField(max_length=240)
    concept = models.TextField(help_text="Plain-text explanation; blank lines split paragraphs")
    formula = models.TextField(blank=True, help_text="LaTeX, rendered with MathJax")
    script = models.CharField(max_length=80, help_text="File in qml_lab/, e.g. m01_qubits.py")
    figure = models.CharField(max_length=80, help_text="PNG the script saves, e.g. m01_bloch.png")
    figure_caption = models.TextField(blank=True)
    checkpoint = models.TextField()
    params = models.JSONField(default=dict, blank=True, help_text="Parameter defaults the script reads via params()")

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return f"Module {self.number}: {self.title}"

    def get_absolute_url(self):
        return reverse("module_detail", args=[self.slug])

    def script_spec(self):
        if not MODULE_SCRIPT.match(self.script or ""):
            raise ScriptUnavailable(f"'{self.script}' is not a module script name like m01_qubits.py.")
        lab = settings.QML_LAB_DIR.resolve()
        return ScriptSpec(label=f"module {self.number}", path=safe_script_path(lab, self.script), cwd=lab,
                          figure=self.figure, params=dict(self.params or {}), pythonpath=(lab,))

    def source_code(self):
        try:
            return self.script_spec().path.read_text(encoding="utf-8")
        except (ScriptUnavailable, OSError, UnicodeDecodeError):
            return ""


class Progress(models.Model):
    """How far one user is with one module."""

    class Status(models.TextChoices):
        NOT_STARTED = "not_started", "Not started"
        IN_PROGRESS = "in_progress", "In progress"
        DONE = "done", "Checkpoint passed"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="progress")
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="progress")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NOT_STARTED)
    notes = models.TextField(blank=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "module"], name="one_progress_per_module")]

    def __str__(self):
        return f"{self.user} · {self.module} · {self.get_status_display()}"
