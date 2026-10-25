"""Read and validate project workspaces. Pure Python (tomllib), no Django.

A workspace is a folder under qml_projects/ named after the project slug:

    qml_projects/<slug>/
        project.toml          metadata + experiments (see README for the format)
        README.md             goal, open questions, ideas: the living part
        experiments/*.py      scripts the portal can run
"""
import tomllib
from dataclasses import dataclass
from pathlib import Path

from core.exceptions import ScriptUnavailable
from core.scripts import safe_script_path, validate_param_defaults

from .constants import DIFFICULTIES, FIGURE_NAME, SLUG, TRACKS

MANIFEST = "project.toml"


class ManifestError(ValueError):
    """A project.toml that cannot be used. Lists every problem, not just the first."""

    def __init__(self, path, problems):
        self.path, self.problems = Path(path), list(problems)
        super().__init__(f"{self.path}: " + "; ".join(self.problems))


@dataclass(frozen=True)
class ExperimentManifest:
    slug: str
    title: str
    script: str
    figure: str = ""
    description: str = ""
    params: dict | None = None


@dataclass(frozen=True)
class ProjectManifest:
    folder: Path
    slug: str
    title: str
    track: str
    difficulty: str
    summary: str
    tools: str = ""
    number: int | None = None
    builds_on: tuple = ()
    experiments: tuple = ()


def load_manifest(folder):
    """Parse and validate folder/project.toml. Raises ManifestError."""
    folder = Path(folder)
    path = folder / MANIFEST
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ManifestError(path, ["file is missing"]) from None
    except (OSError, UnicodeDecodeError) as exc:
        raise ManifestError(path, [f"cannot read file: {exc}"]) from None
    except tomllib.TOMLDecodeError as exc:
        raise ManifestError(path, [f"invalid TOML: {exc}"]) from None

    problems = []
    slug = folder.name
    if not SLUG.match(slug):
        problems.append(f"folder name '{slug}' must be lowercase words joined by '-'")

    def text(key, required=True):
        value = data.get(key, "")
        if not isinstance(value, str):
            problems.append(f"'{key}' must be text")
            return ""
        if required and not value.strip():
            problems.append(f"'{key}' is required")
        return value.strip()

    title, summary, tools = text("title"), text("summary"), text("tools", required=False)
    track, difficulty = text("track"), text("difficulty")
    if track and track not in TRACKS:
        problems.append(f"track '{track}' must be one of: {', '.join(TRACKS)}")
    if difficulty and difficulty not in DIFFICULTIES:
        problems.append(f"difficulty '{difficulty}' must be one of: {', '.join(DIFFICULTIES)}")

    number = data.get("number")
    if number is not None and (isinstance(number, bool) or not isinstance(number, int) or number < 1):
        problems.append("'number' must be a positive whole number")
        number = None
    builds_on = data.get("builds_on", [])
    if not isinstance(builds_on, list) or not all(isinstance(n, int) and not isinstance(n, bool) for n in builds_on):
        problems.append("'builds_on' must be a list of module numbers, e.g. [5, 7]")
        builds_on = []

    experiments, seen = [], set()
    raw_experiments = data.get("experiments", [])
    if not isinstance(raw_experiments, list):
        problems.append("'experiments' must be written as [[experiments]] tables")
        raw_experiments = []
    for i, raw in enumerate(raw_experiments, start=1):
        where = f"experiment {i}"
        if not isinstance(raw, dict):
            problems.append(f"{where} must be a table")
            continue
        e_slug = str(raw.get("slug", "")).strip()
        if not SLUG.match(e_slug):
            problems.append(f"{where}: 'slug' must be lowercase words joined by '-'")
        elif e_slug in seen:
            problems.append(f"{where}: slug '{e_slug}' is used twice")
        seen.add(e_slug)
        where = f"experiment '{e_slug or i}'"
        e_title = str(raw.get("title", "")).strip()
        if not e_title:
            problems.append(f"{where}: 'title' is required")
        script = str(raw.get("script", "")).strip()
        try:
            safe_script_path(folder, script)
        except ScriptUnavailable as exc:
            problems.append(f"{where}: {exc}")
        figure = str(raw.get("figure", "")).strip()
        if figure and not FIGURE_NAME.match(figure):
            problems.append(f"{where}: figure '{figure}' must be a file name like result.png")
        e_params = raw.get("params", {})
        problems += validate_param_defaults(e_params, f"{where} params")
        experiments.append(ExperimentManifest(e_slug, e_title, script, figure,
                                              str(raw.get("description", "")).strip(),
                                              e_params if isinstance(e_params, dict) else {}))

    if problems:
        raise ManifestError(path, problems)
    return ProjectManifest(folder, slug, title, track, difficulty, summary, tools, number,
                           tuple(builds_on), tuple(experiments))


def discover(root):
    """Load every workspace under `root`. Returns (manifests, errors); one bad folder never stops the rest."""
    root = Path(root)
    manifests, errors = [], []
    if not root.is_dir():
        return manifests, [ManifestError(root, ["projects folder does not exist"])]
    for folder in sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith((".", "_"))):
        try:
            manifests.append(load_manifest(folder))
        except ManifestError as exc:
            errors.append(exc)
    numbers = {}
    for m in manifests:
        if m.number is not None:
            numbers.setdefault(m.number, []).append(m.slug)
    for number, slugs in numbers.items():
        if len(slugs) > 1:
            errors.append(ManifestError(root, [f"number {number} is used by {', '.join(slugs)}"]))
    return manifests, errors
