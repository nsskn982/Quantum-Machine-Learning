"""Module 5: a variational quantum classifier (VQC) with data re-uploading."""
import numpy as np
import matplotlib.pyplot as plt
import pennylane as qml
from pennylane import numpy as pnp
from sklearn.model_selection import train_test_split
from plots import save, moons, params, log_metrics

P = params(n_layers=3, epochs=40, batch=25, stepsize=0.1, seed=0)
N_QUBITS, N_LAYERS, EPOCHS, BATCH = 2, P.n_layers, P.epochs, P.batch
X, y = moons(n=200, noise=0.15)
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=1)

dev = qml.device("default.qubit", wires=N_QUBITS)

@qml.qnode(dev)
def circuit(weights, x):
    for layer in range(N_LAYERS):
        qml.AngleEmbedding(x, wires=range(N_QUBITS), rotation="Y")       # encode (again)
        qml.StronglyEntanglingLayers(weights[layer:layer + 1], wires=range(N_QUBITS))  # trainable
    return qml.expval(qml.PauliZ(0))          # a number in [-1, 1]

def model(weights, bias, x):
    return circuit(weights, x) + bias         # x may be a batch: PennyLane broadcasts it

def loss(weights, bias, x, y):
    return pnp.mean((model(weights, bias, x) - y) ** 2)

def accuracy(weights, bias, x, y):
    return np.mean(np.sign(model(weights, bias, x)) == y)

shape = qml.StronglyEntanglingLayers.shape(n_layers=N_LAYERS, n_wires=N_QUBITS)
rng = np.random.default_rng(P.seed)
weights = pnp.array(rng.uniform(0, 2 * np.pi, shape), requires_grad=True)
bias = pnp.array(0.0, requires_grad=True)
print(qml.draw(circuit)(weights, X_tr[0]))

opt = qml.AdamOptimizer(stepsize=P.stepsize)
hist = {"loss": [], "train": [], "test": []}
for epoch in range(EPOCHS):
    order = rng.permutation(len(X_tr))
    for start in range(0, len(X_tr), BATCH):
        idx = order[start:start + BATCH]
        xb, yb = pnp.array(X_tr[idx], requires_grad=False), pnp.array(y_tr[idx], requires_grad=False)
        (weights, bias), _ = opt.step_and_cost(lambda w, b: loss(w, b, xb, yb), weights, bias)
    hist["loss"].append(float(loss(weights, bias, X_tr, y_tr)))
    hist["train"].append(accuracy(weights, bias, X_tr, y_tr))
    hist["test"].append(accuracy(weights, bias, X_te, y_te))
    print(f"epoch {epoch + 1:2d}  loss {hist['loss'][-1]:.3f}  "
          f"train {hist['train'][-1]:.2f}  test {hist['test'][-1]:.2f}")

# Decision boundary: evaluate the model on a grid
g = np.linspace(0, np.pi, 60)
G1, G2 = np.meshgrid(g, g)
Z = np.array(model(weights, bias, np.c_[G1.ravel(), G2.ravel()])).reshape(G1.shape)

fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
axes[0].plot(hist["loss"], label="training loss (MSE)")
axes[0].plot(hist["train"], label="train accuracy")
axes[0].plot(hist["test"], label="test accuracy")
axes[0].set_xlabel("epoch"); axes[0].set_title("VQC training"); axes[0].legend()
cs = axes[1].contourf(G1, G2, Z, levels=20, cmap="coolwarm", alpha=0.7)
axes[1].contour(G1, G2, Z, levels=[0], colors="k")
axes[1].scatter(X_te[:, 0], X_te[:, 1], c=y_te, cmap="coolwarm", edgecolor="k", s=25)
fig.colorbar(cs, ax=axes[1], label="model output ⟨Z⟩ + b")
axes[1].set_title(f"Decision boundary, test accuracy {hist['test'][-1]:.0%}")
save(fig, "m05_vqc")
log_metrics(train_accuracy=hist["train"][-1], test_accuracy=hist["test"][-1], final_loss=hist["loss"][-1])
