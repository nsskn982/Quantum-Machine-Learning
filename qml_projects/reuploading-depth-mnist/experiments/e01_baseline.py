"""Re-uploading classifier on two MNIST-style digits, against logistic regression.

Uses scikit-learn's 8x8 digits (no download). PCA reduces each image to n_qubits
features, which are re-uploaded before every trainable layer.
"""
import matplotlib.pyplot as plt
import numpy as np
import pennylane as qml
from pennylane import numpy as pnp
from sklearn.datasets import load_digits
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler

from plots import log_metrics, params, save

P = params(digit_a=3, digit_b=5, n_qubits=4, n_layers=2, epochs=15, seed=0)
if P.digit_a == P.digit_b or not (0 <= P.digit_a <= 9 and 0 <= P.digit_b <= 9):
    raise SystemExit("digit_a and digit_b must be two different digits from 0 to 9")
if not 1 <= P.n_qubits <= 8:
    raise SystemExit("n_qubits must be between 1 and 8")
if P.n_layers < 1 or P.epochs < 1:
    raise SystemExit("n_layers and epochs must be at least 1")

digits = load_digits()
mask = np.isin(digits.target, [P.digit_a, P.digit_b])
X, y = digits.data[mask], np.where(digits.target[mask] == P.digit_a, -1, 1)
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.3, random_state=P.seed, stratify=y)
pca = PCA(n_components=P.n_qubits, random_state=P.seed).fit(X_tr)
scaler = MinMaxScaler((0, np.pi)).fit(pca.transform(X_tr))
X_tr, X_te = scaler.transform(pca.transform(X_tr)), np.clip(scaler.transform(pca.transform(X_te)), 0, np.pi)
print(f"{len(X_tr)} training and {len(X_te)} test images, {P.n_qubits} PCA features")

dev = qml.device("default.qubit", wires=P.n_qubits)

@qml.qnode(dev)
def circuit(weights, x):
    for layer in range(P.n_layers):
        qml.AngleEmbedding(x, wires=range(P.n_qubits), rotation="Y")
        qml.StronglyEntanglingLayers(weights[layer:layer + 1], wires=range(P.n_qubits))
    return qml.expval(qml.PauliZ(0))

def model(w, b, x):
    return circuit(w, x) + b

def loss(w, b, x, y):
    return pnp.mean((model(w, b, x) - y) ** 2)

def accuracy(w, b, x, y):
    return float(np.mean(np.sign(model(w, b, x)) == y))

rng = np.random.default_rng(P.seed)
shape = qml.StronglyEntanglingLayers.shape(n_layers=P.n_layers, n_wires=P.n_qubits)
w = pnp.array(rng.uniform(0, 2 * np.pi, shape), requires_grad=True)
b = pnp.array(0.0, requires_grad=True)
opt = qml.AdamOptimizer(0.1)
history = {"loss": [], "test": []}
for epoch in range(P.epochs):
    for idx in np.array_split(rng.permutation(len(X_tr)), max(1, len(X_tr) // 32)):
        xb = pnp.array(X_tr[idx], requires_grad=False)
        yb = pnp.array(y_tr[idx], requires_grad=False)
        (w, b), _ = opt.step_and_cost(lambda w_, b_: loss(w_, b_, xb, yb), w, b)
    history["loss"].append(float(loss(w, b, X_tr, y_tr)))
    history["test"].append(accuracy(w, b, X_te, y_te))
    print(f"epoch {epoch + 1:2d}  loss {history['loss'][-1]:.3f}  test {history['test'][-1]:.3f}")

baseline = LogisticRegression(max_iter=1000).fit(X_tr, y_tr).score(X_te, y_te)
n_weights = int(np.prod(shape)) + 1

fig, ax = plt.subplots(figsize=(7, 4))
ax.plot(history["test"], "o-", label=f"re-uploading VQC ({n_weights} weights)")
ax.axhline(baseline, color="k", ls="--", label=f"logistic regression ({P.n_qubits + 1} weights)")
ax.set_xlabel("epoch"); ax.set_ylabel("test accuracy"); ax.set_ylim(0.4, 1.02)
ax.set_title(f"Digits {P.digit_a} vs {P.digit_b}: {P.n_qubits} qubits, {P.n_layers} layers")
ax.legend()
save(fig, "baseline")
log_metrics(test_accuracy=history["test"][-1], baseline_accuracy=baseline,
            final_loss=history["loss"][-1], weights=n_weights)
