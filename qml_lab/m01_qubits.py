"""Module 1: a qubit is a unit vector; gates rotate it on the Bloch sphere."""
import numpy as np
import matplotlib.pyplot as plt
import pennylane as qml
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from plots import save, bloch_vector, draw_sphere

thetas = np.linspace(0, 2 * np.pi, 60)

# --- Qiskit: build a circuit, read its exact state vector -------------------
def qiskit_state(gate, theta):
    qc = QuantumCircuit(1)
    getattr(qc, gate)(theta, 0)           # qc.rx(theta, 0) or qc.ry(theta, 0)
    return Statevector(qc).data           # [a, b] with |a|^2 + |b|^2 = 1

# --- PennyLane: the same circuit as a Python function -----------------------
dev = qml.device("default.qubit", wires=1)

@qml.qnode(dev)
def pl_state(gate, theta):
    {"rx": qml.RX, "ry": qml.RY}[gate](theta, wires=0)
    return qml.state()

# Both frameworks must agree (up to a global phase, here exactly)
for th in [0.3, 1.2, 2.5]:
    assert np.allclose(qiskit_state("ry", th), pl_state("ry", th))
print("Qiskit and PennyLane agree on RY states")

ry_path = np.array([bloch_vector(qiskit_state("ry", t)) for t in thetas])
rx_path = np.array([bloch_vector(pl_state("rx", t)) for t in thetas])

fig = plt.figure(figsize=(11, 4.5))
ax = fig.add_subplot(1, 2, 1, projection="3d")
draw_sphere(ax)
ax.plot(*ry_path.T, lw=2, label="RY(θ): rotates in the x–z plane")
ax.plot(*rx_path.T, lw=2, ls="--", label="RX(θ): rotates in the y–z plane")
ax.legend(loc="upper left", fontsize=8)
ax.set_title("Gates are rotations of the Bloch vector")

ax2 = fig.add_subplot(1, 2, 2)
p0 = np.array([abs(qiskit_state("ry", t)[0]) ** 2 for t in thetas])
ax2.plot(thetas, p0, lw=2, label="P(0) from the state vector")
ax2.plot(thetas, np.cos(thetas / 2) ** 2, "k:", label="cos²(θ/2)")
ax2.set_xlabel("θ (rad)"); ax2.set_ylabel("probability of measuring 0")
ax2.set_title("Born rule: P(0) = |a|²"); ax2.legend()
save(fig, "m01_bloch")
