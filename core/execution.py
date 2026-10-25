"""Run one script in a subprocess and collect what it produced. Pure Python, no Django.

Contract with the scripts (implemented by qml_lab/plots.py):
  * QML_FIG_DIR  - folder to write figures into (a fresh temp folder per run)
  * QML_PARAMS   - JSON object of parameter values
  * metrics.json - optional {name: number} file the script writes into QML_FIG_DIR
"""
import json
import math
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from .exceptions import InvalidParams

DONE, FAILED = "done", "failed"
ERR_TIMEOUT, ERR_EXIT, ERR_START = "timeout", "exit_code", "start_failed"

MAX_OUTPUT = 100_000                 # characters of stdout/stderr kept
FIGURE_SUFFIXES = {".png", ".svg", ".jpg", ".jpeg"}
MAX_FIGURES = 12
MAX_FIGURE_BYTES = 10 * 1024 * 1024


@dataclass
class ExecutionResult:
    status: str                       # DONE or FAILED
    error_kind: str = ""              # "", ERR_TIMEOUT, ERR_EXIT or ERR_START
    output: str = ""
    figures: list = field(default_factory=list)   # [(file name, bytes)], primary figure first
    metrics: dict = field(default_factory=dict)
    returncode: int | None = None


def merge_params(defaults, overrides):
    """Defaults updated with overrides, cast to each default's type.

    Unknown names or values that cannot be converted raise InvalidParams.
    """
    overrides = overrides or {}
    unknown = sorted(set(overrides) - set(defaults))
    if unknown:
        raise InvalidParams(f"Unknown parameter(s): {', '.join(unknown)}. Allowed: {', '.join(defaults) or 'none'}.")
    merged = dict(defaults)
    for name, value in overrides.items():
        kind = type(defaults[name])
        try:
            if kind is bool:
                if isinstance(value, str):
                    if value.strip().lower() not in {"true", "false", "1", "0", "yes", "no", "on", "off"}:
                        raise ValueError(value)
                    value = value.strip().lower() in {"true", "1", "yes", "on"}
                merged[name] = bool(value)
            elif kind is int:
                if isinstance(value, float) and not value.is_integer():
                    raise ValueError(value)
                merged[name] = int(value)
            elif kind is float:
                merged[name] = float(value)
                if not math.isfinite(merged[name]):
                    raise ValueError(value)
            else:
                merged[name] = str(value)
        except (TypeError, ValueError):
            raise InvalidParams(f"Parameter '{name}' must be {kind.__name__}, got {value!r}.") from None
    return merged


def execute(spec, params, timeout, python=None):
    """Run `spec` with `params` and return an ExecutionResult. Never raises for script failures."""
    with tempfile.TemporaryDirectory(prefix="qml-run-") as out_dir:
        env = os.environ.copy()
        extra = [str(p) for p in spec.pythonpath]
        if env.get("PYTHONPATH"):
            extra.append(env["PYTHONPATH"])
        env.update({
            "MPLBACKEND": "Agg",
            "PYTHONUNBUFFERED": "1",
            "QML_FIG_DIR": out_dir,
            "QML_PARAMS": json.dumps(params),
            "PYTHONPATH": os.pathsep.join(extra),
        })
        try:
            proc = subprocess.run(
                [python or sys.executable, str(spec.path)],
                cwd=spec.cwd, env=env, capture_output=True, text=True, timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            partial = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            return ExecutionResult(FAILED, ERR_TIMEOUT, _trim(f"{partial}\nStopped after {timeout} s."))
        except OSError as exc:
            return ExecutionResult(FAILED, ERR_START, f"Could not start the script: {exc}")

        output = proc.stdout + (("\n" + proc.stderr) if proc.stderr else "")
        metrics, warnings = _read_metrics(Path(out_dir))
        figures, fig_warnings = _read_figures(Path(out_dir), spec.figure)
        notes = "".join(f"\n[portal] {w}" for w in warnings + fig_warnings)
        if proc.returncode != 0:
            return ExecutionResult(FAILED, ERR_EXIT, _trim(f"{output}{notes}\n[exit code {proc.returncode}]"),
                                   figures, metrics, proc.returncode)
        return ExecutionResult(DONE, "", _trim(output + notes), figures, metrics, 0)


def _trim(text):
    if len(text) <= MAX_OUTPUT:
        return text
    return "[output trimmed to the last 100 000 characters]\n" + text[-MAX_OUTPUT:]


def _read_metrics(folder):
    path = folder / "metrics.json"
    if not path.exists():
        return {}, []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {}, [f"metrics.json ignored: {exc}"]
    if not isinstance(data, dict):
        return {}, ["metrics.json ignored: it must hold a JSON object."]
    metrics, warnings = {}, []
    for name, value in data.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            warnings.append(f"metric '{name}' ignored: {value!r} is not a finite number.")
        else:
            metrics[str(name)] = value
    return metrics, warnings


def _read_figures(folder, primary):
    files = sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in FIGURE_SUFFIXES)
    files.sort(key=lambda p: p.name != primary)          # primary first, others by name
    figures, warnings = [], []
    for path in files:
        if len(figures) == MAX_FIGURES:
            warnings.append(f"only the first {MAX_FIGURES} figures were kept.")
            break
        if path.stat().st_size > MAX_FIGURE_BYTES:
            warnings.append(f"{path.name} skipped: larger than 10 MB.")
            continue
        figures.append((path.name, path.read_bytes()))
    if primary and not any(name == primary for name, _ in figures):
        warnings.append(f"expected figure {primary} was not produced.")
    return figures, warnings
