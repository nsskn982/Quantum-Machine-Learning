"""Shared helpers for every module and project script.

save()         write a figure (into QML_FIG_DIR when the portal runs the script)
params()       read run parameters; defaults when run by hand
log_metrics()  record numbers (accuracy, loss...) that the portal stores with the run
"""
import json
import os
import sys
from types import SimpleNamespace
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

# The portal sets QML_FIG_DIR so each run gets its own folder; locally, figures/ next to the scripts.
FIG_DIR = Path(os.environ.get("QML_FIG_DIR") or Path(__file__).parent / "figures")
FIG_DIR.mkdir(exist_ok=True)
plt.rcParams.update({"figure.dpi": 120, "axes.grid": True, "grid.alpha": 0.3,
                     "axes.spines.top": False, "axes.spines.right": False})


def save(fig, name):
    """Save a figure to figures/<name>.png and show it."""
    path = FIG_DIR / f"{name}.png"
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    print(f"saved {path}")
    if "agg" not in plt.get_backend().lower():   # headless runs (the portal) skip the window
        plt.show()


def bloch_vector(state):
    """Bloch vector (x, y, z) of a single-qubit state [a, b]."""
    a, b = state
    return np.array([2 * np.real(np.conj(a) * b),
                     2 * np.imag(np.conj(a) * b),
                     abs(a) ** 2 - abs(b) ** 2])


def draw_sphere(ax):
    """Wireframe Bloch sphere with labelled poles on a 3D axis."""
    u, v = np.mgrid[0:2 * np.pi:40j, 0:np.pi:20j]
    ax.plot_wireframe(np.cos(u) * np.sin(v), np.sin(u) * np.sin(v), np.cos(v),
                      color="grey", alpha=0.15, linewidth=0.5)
    for vec, lab in [((0, 0, 1.15), "|0>"), ((0, 0, -1.25), "|1>"),
                     ((1.2, 0, 0), "|+>"), ((0, 1.2, 0), "|+i>")]:
        ax.text(*vec, lab)
    ax.set_box_aspect((1, 1, 1))
    ax.set_xlim(-1, 1); ax.set_ylim(-1, 1); ax.set_zlim(-1, 1)
    ax.set_xlabel("x"); ax.set_ylabel("y"); ax.set_zlabel("z")


def moons(n=200, noise=0.1, seed=0):
    """Two-moons dataset scaled to [0, pi], labels in {-1, +1}."""
    from sklearn.datasets import make_moons
    from sklearn.preprocessing import MinMaxScaler
    X, y = make_moons(n_samples=n, noise=noise, random_state=seed)
    X = MinMaxScaler((0, np.pi)).fit_transform(X)
    return X, 2 * y - 1


_TRUE = {"true", "1", "yes", "on"}


def params(**defaults):
    """Return run parameters as attributes, e.g. P = params(n_layers=3); P.n_layers.

    Run by hand, you get the defaults. Run from the portal, values come from the
    QML_PARAMS environment variable and are cast to each default's type.
    """
    given = {}
    raw = os.environ.get("QML_PARAMS", "")
    if raw:
        try:
            given = json.loads(raw)
        except ValueError:
            print("[plots] QML_PARAMS is not valid JSON; using defaults", file=sys.stderr)
    values = dict(defaults)
    for name, value in given.items():
        if name not in defaults:
            print(f"[plots] ignoring unknown parameter {name!r}", file=sys.stderr)
            continue
        kind = type(defaults[name])
        values[name] = (str(value).lower() in _TRUE) if kind is bool else kind(value)
    print("params:", ", ".join(f"{k}={v}" for k, v in values.items()))
    return SimpleNamespace(**values)


def log_metrics(**metrics):
    """Record numeric results. Saved as metrics.json next to the figures."""
    path = FIG_DIR / "metrics.json"
    current = {}
    if path.exists():
        try:
            current = json.loads(path.read_text())
        except ValueError:
            current = {}
    current.update({name: float(value) for name, value in metrics.items()})
    path.write_text(json.dumps(current, indent=2))
    print("metrics:", ", ".join(f"{k}={v:.4g}" for k, v in current.items()))

