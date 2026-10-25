"""Starting runs: the one place that decides whether a run may start."""
from django.conf import settings
from django.db import transaction

from .exceptions import InvalidParams, RunAlreadyActive, RunRefused, ScriptUnavailable
from .execution import merge_params
from .models import Run, target_field
from .runner import fail_stale_runs, start_run


def can_run_scripts(user):
    if not settings.QML_RUNS_ENABLED or user is None or not user.is_authenticated:
        return False
    return user.is_staff or not settings.QML_RUNS_STAFF_ONLY


def request_run(user, target, params=None):
    """Create a Run for `target` (a Module or Experiment) and start it after commit.

    Raises RunRefused (or RunAlreadyActive, which carries the existing run).
    """
    if not settings.QML_RUNS_ENABLED:
        raise RunRefused("Running scripts is turned off on this server.")
    if not can_run_scripts(user):
        raise RunRefused("Only staff accounts can run scripts here. Download the script and run it locally.")
    try:
        spec = target.script_spec()
        values = merge_params(spec.params, params)
    except (ScriptUnavailable, InvalidParams) as exc:
        raise RunRefused(str(exc)) from exc

    fail_stale_runs()
    with transaction.atomic():
        active = Run.objects.active().for_target(target).select_for_update().first()
        if active:
            raise RunAlreadyActive(active)
        run = Run.objects.create(user=user, params=values, **{target_field(target): target})
        transaction.on_commit(lambda: start_run(run))
    return run
