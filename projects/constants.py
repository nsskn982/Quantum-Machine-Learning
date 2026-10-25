"""Shared vocabularies for projects. Pure Python so manifests can be validated without Django."""
import re

TRACKS = {
    "kernels": "Kernels",
    "variational": "Variational",
    "hybrid": "Hybrid",
    "quantum_data": "Quantum data",
    "noise_hardware": "Noise and hardware",
}
DIFFICULTIES = {"easy": "Easy", "medium": "Medium", "hard": "Hard"}
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FIGURE_NAME = re.compile(r"^[A-Za-z0-9_\-]+\.(png|svg|jpg|jpeg)$")
