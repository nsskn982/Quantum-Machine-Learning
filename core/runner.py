"""Executes Run records in background threads, using core.execution for the actual work.

Background threads suit a personal or lab portal on one machine. To scale out, call
`execute_run(run_id)` from a task queue (Celery, RQ, django-q2) inside `start_run`.
"""
import logging
import threading
from datetime import timedelta

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import close_old_connections, transaction
from django.utils import timezone

from .exceptions import ScriptUnavailable
from .execution import DONE, execute
from .models import Run, RunFigure

log = logging.getLogger("qml.runs")
_slots = threading.BoundedSemaphore(max(1, getattr(settings, "QML_MAX_PARALLEL_RUNS", 1)))


def start_run(run):
    """Start `run` in a background thread and return immediately."""
    thread = threading.Thread(target=execute_run, args=(run.pk,), name=f"qml-run-{run.pk}", daemon=True)
    thread.start()
    return thread


def fail_stale_runs():
    """Fail runs that can no longer be alive (server restart, killed thread). Returns how many."""
    cutoff = timezone.now() - timedelta(seconds=settings.QML_RUN_TIMEOUT + 300)
    count = Run.objects.active().filter(created__lt=cutoff).update(
        status=Run.Status.FAILED,
        error_kind=Run.ErrorKind.STALE,
        finished=timezone.now(),
        output="The run never finished; the server may have restarted while it was running.",
    )
    if count:
        log.warning("Marked %s stale run(s) as failed", count)
    return count


def execute_run(run_id):
    """Run one queued Run to completion. Always leaves the Run in a final state."""
    close_old_connections()
    try:
        run = Run.objects.select_related("module", "experiment__project").get(pk=run_id)
    except Run.DoesNotExist:
        log.error("Run %s vanished before it started", run_id)
        return
    try:
        _execute(run)
    except Exception:
        log.exception("Portal error while executing run %s", run_id)
        _finish(run, Run.Status.FAILED, Run.ErrorKind.PORTAL_ERROR,
                (run.output + "\n" if run.output else "") + "The portal hit an internal error; see the server log.")
    finally:
        close_old_connections()


def _execute(run):
    try:
        spec = run.target.script_spec()
    except ScriptUnavailable as exc:
        _finish(run, Run.Status.FAILED, Run.ErrorKind.MISSING_SCRIPT, str(exc))
        return

    with _slots:
        run.status, run.started = Run.Status.RUNNING, timezone.now()
        run.save(update_fields=["status", "started"])
        log.info("Run %s started: %s %s", run.pk, spec.label, run.params)
        result = execute(spec, run.params, timeout=settings.QML_RUN_TIMEOUT)

    with transaction.atomic():
        for name, data in result.figures:
            RunFigure.objects.create(run=run, name=name, primary=(name == spec.figure),
                                     file=ContentFile(data, name=f"{run.pk}-{name}"))
        run.metrics = result.metrics
        status = Run.Status.DONE if result.status == DONE else Run.Status.FAILED
        _finish(run, status, result.error_kind or Run.ErrorKind.NONE, result.output)
    log.info("Run %s %s in %.1f s", run.pk, run.status, run.duration or 0)


def _finish(run, status, error_kind, output):
    run.status, run.error_kind, run.output, run.finished = status, error_kind, output, timezone.now()
    run.save(update_fields=["status", "error_kind", "output", "metrics", "finished"])
