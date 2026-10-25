"""What a runnable script is, and how its path is validated. Pure Python."""
import re
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from .exceptions import ScriptUnavailable

_SEGMENT = re.compile(r"^[A-Za-z0-9_\-]+$")
PARAM_TYPES = (bool, int, float, str)


@dataclass(frozen=True)
class ScriptSpec:
    """Everything the executor needs to run one script."""

    label: str                       # shown in logs, e.g. "module 5" or "reuploading-depth-mnist/baseline"
    path: Path                       # absolute path of the .py file
    cwd: Path                        # working directory for the run
    figure: str = ""                 # primary figure file name, e.g. "m05_vqc.png"
    params: dict = field(default_factory=dict)          # parameter defaults
    pythonpath: tuple = ()           # extra import folders (qml_lab for plots.py, the workspace)


def safe_script_path(base_dir, relative):
    """Resolve `relative` inside `base_dir`, refusing anything that could escape it.

    Accepts paths such as "m05_vqc.py" or "experiments/e01_baseline.py".
    Raises ScriptUnavailable with a readable reason otherwise.
    """
    if not relative or not isinstance(relative, str):
        raise ScriptUnavailable("No script is set.")
    rel = PurePosixPath(relative)
    if rel.is_absolute() or rel.suffix != ".py":
        raise ScriptUnavailable(f"'{relative}' must be a relative path to a .py file.")
    if not all(_SEGMENT.match(part) for part in [*rel.parts[:-1], rel.stem]):
        raise ScriptUnavailable(f"'{relative}' may only use letters, digits, '_' and '-' (no '..').")
    base = Path(base_dir).resolve()
    path = (base / Path(*rel.parts)).resolve()
    if base not in path.parents:
        raise ScriptUnavailable(f"'{relative}' is outside {base}.")
    if not path.is_file():
        raise ScriptUnavailable(f"'{relative}' was not found in {base}.")
    return path


def validate_param_defaults(params, where="params"):
    """Return a list of problems with a params dict (empty list = valid)."""
    if not isinstance(params, dict):
        return [f"{where} must be a table of name = value pairs."]
    problems = []
    for name, value in params.items():
        if not re.match(r"^[a-z_][a-z0-9_]*$", str(name)):
            problems.append(f"{where}.{name}: names use lowercase letters, digits and '_'.")
        if not isinstance(value, PARAM_TYPES):
            problems.append(f"{where}.{name}: value must be a number, true/false or text.")
    return problems
