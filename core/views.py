import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .exceptions import PortalError, RunAlreadyActive, RunRefused
from .forms import ParamsForm
from .models import Run
from .runner import fail_stale_runs
from .services import request_run

log = logging.getLogger("qml.runs")

ERROR_HELP = {
    Run.ErrorKind.TIMEOUT: "The script ran longer than QML_RUN_TIMEOUT. Try smaller parameters or raise the limit.",
    Run.ErrorKind.EXIT_CODE: "The script raised an error. The traceback is at the end of the output.",
    Run.ErrorKind.START_FAILED: "Python could not start the script. Check the server's Python environment.",
    Run.ErrorKind.MISSING_SCRIPT: "The script file is missing or its path is invalid.",
    Run.ErrorKind.INVALID_PARAMS: "The parameters did not match what the script accepts.",
    Run.ErrorKind.STALE: "The run was interrupted, most likely by a server restart. Start it again.",
    Run.ErrorKind.PORTAL_ERROR: "Something failed inside the portal. The server log has the details.",
}


def start_run_from_request(request, target, on_started=None):
    """Shared POST handler: validate parameters, start a run, redirect.

    Used by module and experiment views so both behave the same way.
    """
    try:
        defaults = target.script_spec().params
    except PortalError as exc:                     # missing or unsafe script
        messages.error(request, str(exc))
        return redirect(target)

    form = ParamsForm(defaults, request.POST)
    if not form.is_valid():
        problems = "; ".join(f"{form.fields[f].label}: {' '.join(e)}" for f, e in form.errors.items())
        messages.error(request, f"Check the parameters. {problems}")
        return redirect(target)
    try:
        run = request_run(request.user, target, form.cleaned_data)
    except RunAlreadyActive as exc:
        messages.info(request, str(exc))
        return redirect(exc.run)
    except RunRefused as exc:
        messages.error(request, str(exc))
        return redirect(target)
    if on_started:
        on_started(run)
    return redirect(run)


@login_required
def run_detail(request, pk):
    run = get_object_or_404(
        Run.objects.select_related("module", "experiment__project", "user").prefetch_related("figures"), pk=pk
    )
    if run.active:
        fail_stale_runs()
        run.refresh_from_db()
    return render(request, "core/run_detail.html", {"run": run, "error_help": ERROR_HELP.get(run.error_kind, "")})
