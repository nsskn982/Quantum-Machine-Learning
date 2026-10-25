"""Module 6: quantum kernels and a quantum SVM (Qiskit)."""
import numpy as np
import matplotlib.pyplot as plt
from qiskit.quantum_info import Statevector
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics.pairwise import rbf_kernel
from plots import save, moons, params, log_metrics

P = params(reps=2, rbf_gamma=1.0)

try:                                     # Qiskit >= 2.1 prefers the function form
    from qiskit.circuit.library import zz_feature_map
    feature_map = zz_feature_map(feature_dimension=2, reps=P.reps)
except ImportError:
    from qiskit.circuit.library import ZZFeatureMap
    feature_map = ZZFeatureMap(feature_dimension=2, reps=P.reps)
print(feature_map.decompose().draw())

X, y = moons(n=200, noise=0.15)
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=1)

def states(X):
    """Encode every row of X with the feature map; return the state vectors."""
    return np.array([Statevector(feature_map.assign_parameters(x)).data for x in X])

def quantum_kernel(A, B):
    """K[i, j] = |<psi(a_i)|psi(b_j)>|^2  (fidelity between encoded points)."""
    return np.abs(states(A).conj() @ states(B).T) ** 2

K_tr = quantum_kernel(X_tr, X_tr)
K_te = quantum_kernel(X_te, X_tr)

qsvm = SVC(kernel="precomputed").fit(K_tr, y_tr)
classical = SVC(kernel="rbf", gamma=P.rbf_gamma).fit(X_tr, y_tr)
q_acc = qsvm.score(K_te, y_te)
c_acc = classical.score(X_te, y_te)
print(f"quantum-kernel SVM test accuracy: {q_acc:.2f}")
print(f"classical RBF SVM test accuracy:  {c_acc:.2f}")

# Sort by class so a good kernel shows two bright diagonal blocks
order = np.argsort(y_tr)
fig, axes = plt.subplots(1, 3, figsize=(15, 4.3))
for ax, K, title in [(axes[0], K_tr, f"ZZ quantum kernel (test acc {q_acc:.0%})"),
                     (axes[1], rbf_kernel(X_tr, gamma=P.rbf_gamma), f"Classical RBF kernel (test acc {c_acc:.0%})")]:
    im = ax.imshow(K[np.ix_(order, order)], cmap="magma", vmin=0, vmax=1)
    n0 = np.sum(y_tr == -1)
    ax.axhline(n0 - .5, color="w", lw=.8); ax.axvline(n0 - .5, color="w", lw=.8)
    ax.set_title(title); ax.set_xlabel("training point (sorted by class)")
    fig.colorbar(im, ax=ax, fraction=0.046)

same = K_tr[y_tr[:, None] == y_tr[None, :]]
diff = K_tr[y_tr[:, None] != y_tr[None, :]]
axes[2].hist(same, bins=30, alpha=.6, density=True, label="same class")
axes[2].hist(diff, bins=30, alpha=.6, density=True, label="different class")
axes[2].set_xlabel("kernel value k(x, x')"); axes[2].set_title("Does the kernel separate classes?")
axes[2].legend()
save(fig, "m06_kernels")
log_metrics(quantum_test_accuracy=q_acc, rbf_test_accuracy=c_acc)

# Same thing with the library, for reference (qiskit-machine-learning):
# from qiskit_machine_learning.kernels import FidelityQuantumKernel
# from qiskit_machine_learning.algorithms import QSVC
# qsvc = QSVC(quantum_kernel=FidelityQuantumKernel(feature_map=feature_map)).fit(X_tr, y_tr)
