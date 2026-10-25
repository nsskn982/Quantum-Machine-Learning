# QML Lab portal

A Django portal for the 10-week quantum machine learning plan and the open-ended projects that follow it.

- **Modules**: the 8 learning modules, each with its concept, formula, checkpoint and script. Staff can run a script with parameters and see its figures and metrics.
- **Projects**: open-ended research workspaces. Each project has a folder of code, a plan with open questions, experiments you can run, a team and a journal. Projects are never "done": they stay open, get paused, or get archived.

Requires Python 3.11+ and Django 5.1+.

## Run it

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py seed_portal         # 8 modules + the 16 project workspaces (safe to re-run)
python manage.py createsuperuser     # staff account: needed to run scripts and use /admin
python manage.py test                # 54 tests
python manage.py runserver
```

If you ran an earlier version of the portal, delete `db.sqlite3` and `media/` first: the database layout changed.

## How it is organised

```
core/            running scripts, shared by modules and projects
  scripts.py       ScriptSpec + safe path checks              (pure Python)
  execution.py     subprocess, params, figures, metrics       (pure Python)
  exceptions.py    PortalError, ScriptUnavailable, RunRefused (pure Python)
  runner.py        background execution of Run records, stale-run cleanup
  services.py      request_run(): the single place that decides if a run may start
  views.py         run page + the shared "start a run" POST handler
learning/        Module and Progress; module texts in content.py
projects/        Project, Experiment, Entry (journal)
  manifests.py     reads and validates project.toml           (pure Python)
  scaffold.py      creates a new workspace from a template    (pure Python)
  sync.py          workspaces on disk -> database
qml_lab/         module scripts m01..m08 and plots.py (save, params, log_metrics)
qml_projects/    one folder per project (the open-ended part), each with its LaTeX document in docs/
docs/            overview document, shared LaTeX style + bibliography, build script, PDFs
```

Anything that can be run implements `script_spec()` and returns a `ScriptSpec`. `Module` and `Experiment` both do, so the runner, the run page, parameters and metrics work the same for both. To make something new runnable, give it a `script_spec()` method and a foreign key on `core.Run`.

The pure-Python parts have no Django imports, so their tests also run on their own:

```bash
python -m unittest core.tests.test_execution projects.tests.test_manifests
```

## Documents

Every project has a LaTeX document in `qml_projects/<slug>/docs/main.tex`, and `docs/overview/`
holds the overview of the four quadrants of QML. All use Harvard referencing and one shared
bibliography. Build all PDFs (into `docs/pdf/`) with:

```bash
bash docs/build_all.sh
```

See `docs/README.md` for citing and editing.

## Project workspaces

```
qml_projects/reuploading-depth-mnist/
  project.toml          what the portal reads
  README.md             goal, open questions, ideas: shown on the project page
  experiments/
    e01_baseline.py     a runnable experiment
  docs/
    main.tex            the project's LaTeX document (Harvard references), main.pdf compiled
```

`project.toml`:

```toml
number = 4
title = "Re-uploading depth study on MNIST"
track = "variational"          # kernels | variational | hybrid | quantum_data | noise_hardware
difficulty = "easy"            # easy | medium | hard
tools = "PennyLane, scikit-learn"
builds_on = [5]                # module numbers
summary = "One sentence."

[[experiments]]
slug = "baseline"
title = "Re-uploading classifier vs logistic regression"
script = "experiments/e01_baseline.py"
figure = "baseline.png"        # the figure shown first
description = "Optional."

[experiments.params]           # becomes the run form; numbers, true/false or text
n_layers = 2
epochs = 15
```

Adding to a project:

1. Write a script in `experiments/`. Use `from plots import params, save, log_metrics`. `params()` gives the defaults when you run it by hand and the form values when the portal runs it.
2. Add an `[[experiments]]` block to `project.toml`.
3. Run `python manage.py sync_projects`. The experiment appears with a run form, and every run's parameters and metrics land in a table you can compare.

Syncing only updates descriptions and experiments from disk. Status, lead, members, journal and runs live in the database and are never overwritten. An experiment removed from `project.toml` is hidden, and its runs are kept.

New project:

```bash
python manage.py new_project quantum-walk-search --title "Quantum walk search" \
    --track variational --difficulty hard --summary "Search with quantum walks" --builds-on 3 5
```

A project added on the website gets a workspace the same way: `python manage.py new_project <its-slug>` reuses its details. Each new workspace starts with a runnable starter experiment.

## Error handling

| Where | What happens |
| --- | --- |
| Invalid `project.toml` | `sync_projects` lists every problem in that file and still syncs the other projects; `--strict` makes it fail (for CI) |
| Bad run parameters | The form says which field is wrong; nothing is started |
| No permission, runs turned off, missing script | `RunRefused` with a plain message on the page |
| Same thing already running | You are taken to the existing run |
| Script raises an error | Run is marked *Script error*, and the traceback is in the output |
| Script runs too long | Stopped after `QML_RUN_TIMEOUT`, marked *Timed out*, partial output kept |
| Bad `metrics.json` or missing figure | Run still succeeds; a `[portal]` warning is added to the output |
| Server restarted mid-run | Run is marked *Interrupted* once it is older than the timeout, so it never blocks |
| Bug inside the portal | Run is marked *Portal error*, the traceback goes to the `qml.runs` log, and a run never stays "running" |
| Unknown page / server error | Friendly 404 and 500 pages |

## Settings (environment variables)

| Variable | Default | What it does |
| --- | --- | --- |
| `DJANGO_DEBUG` | `1` | Set `0` in production; then `DJANGO_SECRET_KEY` is required and cookies are HTTPS-only |
| `DJANGO_SECRET_KEY` | dev key | Required when `DJANGO_DEBUG=0` |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated host names |
| `QML_RUNS_ENABLED` | `1` | `0` turns running off for everyone |
| `QML_RUNS_STAFF_ONLY` | `1` | Only staff may run scripts. Set `0` to let project members run their experiments |
| `QML_MAX_PARALLEL_RUNS` | `1` | Scripts running at the same time |
| `QML_RUN_TIMEOUT` | `900` | Seconds before a run is stopped |
| `QML_SIGNUP_ENABLED` | `1` | `0` closes self-registration |
| `QML_PROJECTS_DIR` | `qml_projects/` | Where workspaces live, e.g. a separate Git repository |
| `QML_LOG_LEVEL` | `INFO` | Level for the `qml.*` loggers |

## Before you put it online

Running a script executes code on the server, so only trusted accounts should be able to run (the default is staff only). Also set `DJANGO_DEBUG=0`, `DJANGO_SECRET_KEY` and `DJANGO_ALLOWED_HOSTS`, and serve over HTTPS. For more than a few users, call `core.runner.execute_run` from a task queue (Celery, RQ, django-q2) inside `start_run`, and use PostgreSQL. Run `python manage.py makemigrations --check --dry-run` once; it should print "No changes detected".
