"""Module 2: gates, entanglement and measurement statistics (Qiskit)."""
import numpy as np
import matplotlib.pyplot as plt
from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler
from qiskit.quantum_info import Statevector, SparsePauliOp
from plots import save

SHOTS = 2000
sampler = StatevectorSampler(seed=7)

def counts(qc):
    """Run a measured circuit and return {bitstring: count}."""
    result = sampler.run([qc], shots=SHOTS).result()
    return result[0].data.meas.get_counts()   # 'meas' = register from measure_all

# Product state: two independent coin flips
product = QuantumCircuit(2)
product.h([0, 1])

# Bell state: H then CNOT entangles the qubits
bell = QuantumCircuit(2)
bell.h(0)
bell.cx(0, 1)
print(bell.draw())                            # text diagram of the circuit

def measured(qc):
    m = qc.copy()
    m.measure_all()
    return m

c_prod, c_bell = counts(measured(product)), counts(measured(bell))
labels = ["00", "01", "10", "11"]               # Qiskit order: qubit 1 is the left bit

# Correlation <Z⊗Z> when qubit 1 is rotated by RY(θ) before measuring
ZZ = SparsePauliOp("ZZ")
thetas = np.linspace(0, 2 * np.pi, 80)
def zz(base, th):
    qc = base.copy()
    qc.ry(th, 1)
    return Statevector(qc).expectation_value(ZZ).real
corr_bell = [zz(bell, t) for t in thetas]
corr_prod = [zz(product, t) for t in thetas]

fig, axes = plt.subplots(1, 3, figsize=(13, 3.8))
for ax, c, title in [(axes[0], c_prod, "H ⊗ H: four equal outcomes"),
                     (axes[1], c_bell, "Bell state: only 00 and 11")]:
    ax.bar(labels, [c.get(k, 0) / SHOTS for k in labels])
    ax.set_ylim(0, 0.6); ax.set_title(title); ax.set_ylabel("frequency")
axes[2].plot(thetas, corr_bell, lw=2, label="Bell state")
axes[2].plot(thetas, corr_prod, lw=2, ls="--", label="product state")
axes[2].plot(thetas, np.cos(thetas), "k:", label="cos θ")
axes[2].set_xlabel("θ on qubit 1 (rad)"); axes[2].set_ylabel("⟨Z⊗Z⟩")
axes[2].set_title("Entangled qubits stay correlated"); axes[2].legend(fontsize=8)
save(fig, "m02_entanglement")
