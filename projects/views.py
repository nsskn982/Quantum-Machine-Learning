from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Prefetch, Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.forms import ParamsForm
from core.models import Run
from core.views import start_run_from_request

from .forms import EntryForm, ProjectCreateForm, ProjectSettingsForm
from .models import Entry, Experiment, Project

FILTERS = {"track": Project._meta.get_field("track").choices,
           "difficulty": Project._meta.get_field("difficulty").choices,
           "status": Project.Status.choices}


def members_only(view):
    """POST views that only project members may use. Passes the project in."""
    @wraps(view)
    def wrapper(request, slug, *args, **kwargs):
        project = get_object_or_404(Project, slug=slug)
        if not project.is_member(request.user):
            messages.error(request, "Join the project first.")
            return redirect(project)
        return view(request, project, *args, **kwargs)
    return login_required(require_POST(wrapper))


@login_required
def project_list(request):
    projects = (Project.objects.select_related("lead").prefetch_related("builds_on")
                .annotate(member_count=Count("members", distinct=True), run_count=Count("experiments__runs", distinct=True)))
    active = {}
    for field, choices in FILTERS.items():
        value = request.GET.get(field, "")
        if value in dict(choices):
            projects = projects.filter(**{field: value})
            active[field] = value
    if "status" not in active:
        projects = projects.exclude(status=Project.Status.ARCHIVED)
    query = request.GET.get("q", "").strip()[:100]
    if query:
        projects = projects.filter(Q(title__icontains=query) | Q(summary__icontains=query) | Q(tools__icontains=query))
    filters = [{"name": f, "label": f.title(), "choices": c, "value": active.get(f, "")} for f, c in FILTERS.items()]
    return render(request, "projects/project_list.html",
                  {"projects": projects, "filters": filters, "query": query, "filtered": bool(active or query)})


@login_required
def project_detail(request, slug):
    recent_runs = Run.objects.select_related("user").prefetch_related("figures")
    project = get_object_or_404(Project.objects.select_related("lead"), slug=slug)
    experiments = project.experiments.filter(active=True).prefetch_related(
        Prefetch("runs", queryset=recent_runs, to_attr="all_runs")
    )
    is_member = project.is_member(request.user)
    rows = []
    for exp in experiments:
        runs = exp.all_runs[:8]
        metric_names = sorted({name for r in runs for name in (r.metrics or {})})
        rows.append({"exp": exp, "form": ParamsForm(exp.params), "runs": runs, "metric_names": metric_names,
                     "latest": next((r for r in runs if r.status == Run.Status.DONE and r.primary_figure), None)})
    context = {
        "project": project,
        "is_member": is_member,
        "members": project.members.all(),
        "readme": project.readme(),
        "experiments": rows,
        "entries": project.entries.select_related("author", "run")[:50],
        "entry_form": EntryForm() if is_member else None,
        "settings_form": ProjectSettingsForm(instance=project) if is_member else None,
        "has_workspace": project.workspace_path() is not None,
    }
    return render(request, "projects/project_detail.html", context)


@login_required
def project_create(request):
    form = ProjectCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        project = form.save()
        project.members.add(request.user)
        project.lead = request.user
        project.save(update_fields=["lead"])
        messages.success(request, f"Project added. To give it a code workspace, run: "
                                  f"python manage.py new_project {project.slug}")
        return redirect(project)
    return render(request, "projects/project_form.html", {"form": form})


@login_required
@require_POST
def project_join(request, slug):
    project = get_object_or_404(Project, slug=slug)
    if project.status == Project.Status.ARCHIVED:
        messages.error(request, "This project is archived. Ask a member to reopen it.")
        return redirect(project)
    project.members.add(request.user)
    changed = []
    if project.lead_id is None:
        project.lead = request.user
        changed.append("lead")
    if project.status == Project.Status.OPEN:
        project.status = Project.Status.ACTIVE
        changed.append("status")
    if changed:
        project.save(update_fields=changed + ["updated"])
    messages.success(request, "You joined the project. It now shows on your dashboard.")
    return redirect(project)


@members_only
def project_leave(request, project):
    project.members.remove(request.user)
    if project.lead_id == request.user.id:
        project.lead = project.members.order_by("pk").first()
        project.save(update_fields=["lead", "updated"])
    if not project.members.exists() and project.status == Project.Status.ACTIVE:
        project.status = Project.Status.OPEN
        project.save(update_fields=["status", "updated"])
    messages.info(request, "You left the project. Your journal entries stay.")
    return redirect(project)


@members_only
def project_settings(request, project):
    form = ProjectSettingsForm(request.POST, instance=project)
    if form.is_valid():
        form.save()
        messages.success(request, "Project settings saved.")
    else:
        messages.error(request, "Settings not saved: " + "; ".join(" ".join(e) for e in form.errors.values()))
    return redirect(project)


@members_only
def entry_create(request, project):
    form = EntryForm(request.POST)
    if form.is_valid():
        entry = form.save(commit=False)
        entry.project, entry.author = project, request.user
        run_id = request.POST.get("run")
        if run_id and run_id.isdigit():
            entry.run = Run.objects.filter(pk=run_id, experiment__project=project).first()
        entry.save()
        messages.success(request, "Added to the journal.")
    else:
        messages.error(request, "The journal entry needs some text.")
    return redirect(f"{project.get_absolute_url()}#journal")


def _experiment(slug, exp):
    return get_object_or_404(Experiment.objects.select_related("project"), project__slug=slug, slug=exp, active=True)


@login_required
@require_POST
def experiment_run(request, slug, exp):
    experiment = _experiment(slug, exp)
    if not experiment.project.is_member(request.user) and not request.user.is_staff:
        messages.error(request, "Join the project to run its experiments.")
        return redirect(experiment.project)

    def log_to_journal(run):
        Entry.objects.create(project=experiment.project, author=request.user, kind=Entry.Kind.NOTE, run=run,
                             text=f"Started {experiment.title} with {run.params or 'default parameters'}.")

    return start_run_from_request(request, experiment, on_started=log_to_journal)


@login_required
def experiment_script(request, slug, exp):
    experiment = _experiment(slug, exp)
    code = experiment.source_code()
    if not code:
        raise Http404("Script not found")
    response = HttpResponse(code, content_type="text/x-python; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{experiment.script.rsplit("/", 1)[-1]}"'
    return response
