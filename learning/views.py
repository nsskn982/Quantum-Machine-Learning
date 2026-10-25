from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Exists, OuterRef, Subquery
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.forms import ParamsForm
from core.models import Run, RunFigure
from core.views import start_run_from_request
from projects.models import Project

from .forms import ProgressForm
from .models import Module, Progress


def signup(request):
    if not settings.QML_SIGNUP_ENABLED:
        raise Http404("Sign-up is closed on this portal.")
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = UserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Account created. Start with Module 1.")
        return redirect("dashboard")
    return render(request, "registration/signup.html", {"form": form})


def latest_figure_runs():
    """{module_id: latest finished module Run that has a figure}, in a few queries."""
    with_figure = Exists(RunFigure.objects.filter(run=OuterRef("pk")))
    latest = (Run.objects.filter(module=OuterRef("pk"), status=Run.Status.DONE).filter(with_figure)
              .order_by("-created").values("pk")[:1])
    ids = [i for i in Module.objects.annotate(run_id=Subquery(latest)).values_list("run_id", flat=True) if i]
    runs = Run.objects.filter(pk__in=ids).prefetch_related("figures")
    return {run.module_id: run for run in runs}


@login_required
def dashboard(request):
    modules = list(Module.objects.all())
    status = dict(Progress.objects.filter(user=request.user).values_list("module_id", "status"))
    latest = latest_figure_runs()
    rows = [{"module": m, "status": status.get(m.pk, Progress.Status.NOT_STARTED), "run": latest.get(m.pk)}
            for m in modules]
    done = sum(1 for r in rows if r["status"] == Progress.Status.DONE)
    context = {
        "rows": rows,
        "done": done,
        "total": len(rows),
        "percent": round(100 * done / len(rows)) if rows else 0,
        "next_row": next((r for r in rows if r["status"] != Progress.Status.DONE), None),
        "my_projects": request.user.qml_projects.exclude(status=Project.Status.ARCHIVED),
    }
    return render(request, "learning/dashboard.html", context)


@login_required
def module_detail(request, slug):
    module = get_object_or_404(Module, slug=slug)
    # Viewing is not progress: a Progress row is only written when the user saves.
    progress = Progress.objects.filter(user=request.user, module=module).first() or Progress(
        user=request.user, module=module
    )
    form = ProgressForm(request.POST or None, instance=progress)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Progress saved.")
            return redirect(module)
        messages.error(request, "Progress not saved. Check the form.")
    runs = module.runs.select_related("user").prefetch_related("figures")[:6]
    context = {
        "module": module,
        "form": form,
        "params_form": ParamsForm(module.params),
        "paragraphs": [p.strip() for p in module.concept.split("\n\n") if p.strip()],
        "runs": runs,
        "latest": next((r for r in runs if r.status == Run.Status.DONE and r.primary_figure), None),
        "source": module.source_code(),
        "runs_enabled": settings.QML_RUNS_ENABLED,
        "previous": Module.objects.filter(number__lt=module.number).last(),
        "next": Module.objects.filter(number__gt=module.number).first(),
        "related_projects": module.projects.exclude(status=Project.Status.ARCHIVED),
    }
    return render(request, "learning/module_detail.html", context)


@login_required
@require_POST
def module_run(request, slug):
    module = get_object_or_404(Module, slug=slug)

    def mark_in_progress(run):
        progress, _ = Progress.objects.get_or_create(user=request.user, module=module)
        if progress.status == Progress.Status.NOT_STARTED:
            progress.status = Progress.Status.IN_PROGRESS
            progress.save(update_fields=["status", "updated"])

    return start_run_from_request(request, module, on_started=mark_in_progress)


@login_required
def download_script(request, slug):
    module = get_object_or_404(Module, slug=slug)
    code = module.source_code()
    if not code:
        raise Http404("Script not found")
    response = HttpResponse(code, content_type="text/x-python; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{module.script}"'
    return response
