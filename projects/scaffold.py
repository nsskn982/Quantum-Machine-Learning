"""Create a new project workspace from a template. Pure Python, no Django."""
import json
from pathlib import Path

from .constants import DIFFICULTIES, SLUG, TRACKS
from .manifests import load_manifest


def toml_str(value):
    """TOML basic string. JSON string escaping is valid TOML for these characters."""
    return json.dumps(str(value), ensure_ascii=False)


def render_manifest(title, track, difficulty, summary, tools="", number=None, builds_on=(), experiments=()):
    lines = []
    if number is not None:
        lines.append(f"number = {int(number)}")
    lines += [
        f"title = {toml_str(title)}",
        f"track = {toml_str(track)}            # {' | '.join(TRACKS)}",
        f"difficulty = {toml_str(difficulty)}  # {' | '.join(DIFFICULTIES)}",
        f"tools = {toml_str(tools)}",
        f"builds_on = [{', '.join(str(int(n)) for n in builds_on)}]  # module numbers",
        f"summary = {toml_str(summary)}",
    ]
    for exp in experiments:
        lines += ["", "[[experiments]]",
                  f"slug = {toml_str(exp['slug'])}",
                  f"title = {toml_str(exp['title'])}",
                  f"script = {toml_str(exp['script'])}"]
        if exp.get("figure"):
            lines.append(f"figure = {toml_str(exp['figure'])}")
        if exp.get("description"):
            lines.append(f"description = {toml_str(exp['description'])}")
        if exp.get("params"):
            lines += ["", "[experiments.params]"]
            for name, value in exp["params"].items():
                lines.append(f"{name} = {_toml_value(value)}")
    return "\n".join(lines) + "\n"


def _toml_value(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    return toml_str(value)


STARTER_SCRIPT = '''"""Starter experiment for {title}. Replace the body with your own work.

Run by hand:     python experiments/e01_starter.py   (from the project folder, with qml_lab on PYTHONPATH)
Run in portal:   the parameters below appear as a form on the project page.
"""
import matplotlib.pyplot as plt
import numpy as np

from plots import log_metrics, params, save

P = params(n_qubits=2, seed=0)
rng = np.random.default_rng(P.seed)

# TODO: build the model and the classical baseline here.
x = np.arange(10)
fig, ax = plt.subplots(figsize=(5, 3))
ax.plot(x, rng.normal(size=10).cumsum(), "o-")
ax.set_title("Starter figure: replace me")
save(fig, "starter")
log_metrics(placeholder=float(P.n_qubits))
'''

README_TEMPLATE = """# {title}

{summary}

## Goal

What question does this project answer, and how will you know?

## Open questions

- 

## Ideas to try

- 

## Log

Record results and decisions in the portal journal; keep this file for the plan.
"""


def create_workspace(root, slug, title, track, difficulty, summary, tools="", number=None, builds_on=()):
    """Create qml_projects/<slug>/ with a manifest, README and one runnable starter experiment."""
    if not SLUG.match(slug):
        raise ValueError(f"slug '{slug}' must be lowercase words joined by '-'")
    if track not in TRACKS:
        raise ValueError(f"track must be one of: {', '.join(TRACKS)}")
    if difficulty not in DIFFICULTIES:
        raise ValueError(f"difficulty must be one of: {', '.join(DIFFICULTIES)}")
    folder = Path(root) / slug
    if folder.exists():
        raise FileExistsError(f"{folder} already exists")
    (folder / "experiments").mkdir(parents=True)
    (folder / "experiments" / "e01_starter.py").write_text(STARTER_SCRIPT.format(title=title), encoding="utf-8")
    (folder / "README.md").write_text(README_TEMPLATE.format(title=title, summary=summary), encoding="utf-8")
    starter = {"slug": "starter", "title": "Starter experiment", "script": "experiments/e01_starter.py",
               "figure": "starter.png", "description": "Template to replace with the first real experiment.",
               "params": {"n_qubits": 2, "seed": 0}}
    (folder / "project.toml").write_text(
        render_manifest(title, track, difficulty, summary, tools, number, builds_on, [starter]), encoding="utf-8"
    )
    load_manifest(folder)          # fail loudly if the template itself is broken
    return folder
