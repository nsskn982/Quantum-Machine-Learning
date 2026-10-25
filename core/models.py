from django.conf import settings
from django.db import models
from django.urls import reverse


class RunQuerySet(models.QuerySet):
    def active(self):
        return self.filter(status__in=[Run.Status.QUEUED, Run.Status.RUNNING])

    def for_target(self, target):
        return self.filter(**{target_field(target): target})


def target_field(target):
    """'module' or 'experiment': the Run field that points at this target."""
    name = target._meta.model_name
    if name not in ("module", "experiment"):
        raise TypeError(f"Cannot run a {name}.")
    return name


class Run(models.Model):
    """One execution of a module script or a project experiment."""

    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        RUNNING = "running", "Running"
        DONE = "done", "Finished"
        FAILED = "failed", "Failed"

    class ErrorKind(models.TextChoices):
        NONE = "", "No error"
        TIMEOUT = "timeout", "Timed out"
        EXIT_CODE = "exit_code", "Script error"
        START_FAILED = "start_failed", "Could not start"
        MISSING_SCRIPT = "missing_script", "Script missing"
        INVALID_PARAMS = "invalid_params", "Invalid parameters"
        STALE = "stale", "Interrupted"
        PORTAL_ERROR = "portal_error", "Portal error"

    module = models.ForeignKey("learning.Module", null=True, blank=True, on_delete=models.CASCADE, related_name="runs")
    experiment = models.ForeignKey(
        "projects.Experiment", null=True, blank=True, on_delete=models.CASCADE, related_name="runs"
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.QUEUED)
    error_kind = models.CharField(max_length=20, choices=ErrorKind.choices, default=ErrorKind.NONE, blank=True)
    params = models.JSONField(default=dict, blank=True)
    metrics = models.JSONField(default=dict, blank=True)
    output = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    started = models.DateTimeField(null=True, blank=True)
    finished = models.DateTimeField(null=True, blank=True)

    objects = RunQuerySet.as_manager()

    class Meta:
        ordering = ["-created"]
        constraints = [
            models.CheckConstraint(
                condition=(models.Q(module__isnull=False, experiment__isnull=True)
                           | models.Q(module__isnull=True, experiment__isnull=False)),
                name="run_has_exactly_one_target",
            )
        ]

    def __str__(self):
        return f"Run {self.pk} of {self.target} ({self.status})"

    def get_absolute_url(self):
        return reverse("run_detail", args=[self.pk])

    @property
    def target(self):
        return self.module or self.experiment

    @property
    def active(self):
        return self.status in (self.Status.QUEUED, self.Status.RUNNING)

    @property
    def duration(self):
        if self.started and self.finished:
            return (self.finished - self.started).total_seconds()
        return None

    @property
    def primary_figure(self):
        figures = list(self.figures.all())          # uses prefetch_related when present
        return figures[0] if figures else None


class RunFigure(models.Model):
    run = models.ForeignKey(Run, on_delete=models.CASCADE, related_name="figures")
    name = models.CharField(max_length=120)
    file = models.FileField(upload_to="runs/%Y/%m/")
    primary = models.BooleanField(default=False)

    class Meta:
        ordering = ["-primary", "name"]

    def __str__(self):
        return self.name
