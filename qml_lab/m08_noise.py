"""Module 8: barren plateaus and hardware noise."""
from functools import reduce
import numpy as np
import matplotlib.pyplot as plt
import pennylane as qml
from pennylane import numpy as pnp
from plots import save, params, log_metrics

P = params(layers=10, samples=100, max_qubits=10, seed=0)
rng = np.random.default_rng(P.seed)
LAYERS, SAMPLES = P.layers, P.samples
QUBITS = list(range(2, max(P.max_qubits, 2) + 1, 2))

# --- A. Barren plateaus: gradient variance vs qubit count -------------------
def grad_variance(n, global_cost):
    dev = qml.device("default.qubit", wires=n)
    obs = (reduce(lambda a, b: a @ b, [qml.PauliZ(i) for i in range(n)])
           if global_cost else qml.PauliZ(0) @ qml.PauliZ(1))

    @qml.qnode(dev)
    def cost(params):
        for layer in range(LAYERS):              # "hardware-efficient" ansatz
            for w in range(n):
                qml.RY(params[layer, w, 0], wires=w)
                qml.RZ(params[layer, w, 1], wires=w)
            for w in range(n - 1):
                qml.CZ(wires=[w, w + 1])
        return qml.expval(obs)

    grads = []
    for _ in range(SAMPLES):                     # random initialisations
        p = pnp.array(rng.uniform(0, 2 * np.pi, (LAYERS, n, 2)), requires_grad=True)
        grads.append(qml.grad(cost)(p)[0, 0, 0])  # dC/d(first angle)
    return np.var(grads)

var_global = [grad_variance(n, True) for n in QUBITS]
var_local = [grad_variance(n, False) for n in QUBITS]
for n, g, l in zip(QUBITS, var_global, var_local):
    print(f"{n:2d} qubits  Var[grad] global {g:.2e}  local {l:.2e}")

# --- B. Noise: a signal that should stay at 1 decays with depth -------------
noisy = qml.device("default.mixed", wires=2)

@qml.qnode(noisy)
def bell_after(depth, p):
    qml.Hadamard(0); qml.CNOT(wires=[0, 1])      # Bell state, <Z Z> = 1
    for _ in range(depth):                       # two CNOTs = identity, ideally
        for _ in range(2):
            qml.CNOT(wires=[0, 1])
            qml.DepolarizingChannel(p, wires=0)
            qml.DepolarizingChannel(p, wires=1)
    return qml.expval(qml.PauliZ(0) @ qml.PauliZ(1))

depths = np.arange(0, 21)
fig, axes = plt.subplots(1, 2, figsize=(12, 4.2))
axes[0].semilogy(QUBITS, var_global, "o-", label="global cost Z⊗Z⊗…⊗Z")
axes[0].semilogy(QUBITS, var_local, "s-", label="local cost Z₀Z₁")
axes[0].set_xlabel("number of qubits"); axes[0].set_ylabel("Var[∂C/∂θ] (log scale)")
axes[0].set_title(f"Barren plateau: gradients vanish ({LAYERS} layers)"); axes[0].legend()
for p in [0.005, 0.01, 0.03]:
    axes[1].plot(depths, [bell_after(d, p) for d in depths], "o-", ms=3, label=f"p = {p}")
axes[1].axhline(1, color="k", ls=":", label="noise-free")
axes[1].set_xlabel("circuit depth (pairs of CNOTs)"); axes[1].set_ylabel("⟨Z⊗Z⟩")
axes[1].set_title("Depolarizing noise erases the signal"); axes[1].legend()
save(fig, "m08_noise")

# --- C. Same idea in Qiskit Aer, with shot counts ---------------------------
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error

noise = NoiseModel()
noise.add_all_qubit_quantum_error(depolarizing_error(0.01, 1), ["h"])
noise.add_all_qubit_quantum_error(depolarizing_error(0.05, 2), ["cx"])
qc = QuantumCircuit(2); qc.h(0); qc.cx(0, 1); qc.measure_all()
sim = AerSimulator(noise_model=noise)
counts = sim.run(transpile(qc, sim), shots=2000).result().get_counts()
print("noisy Bell counts:", counts)
log_metrics(grad_var_global_max_qubits=var_global[-1], grad_var_local_max_qubits=var_local[-1],
            bell_error_rate=(counts.get("01", 0) + counts.get("10", 0)) / 2000)
