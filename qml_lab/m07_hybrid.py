"""Module 7: a hybrid quantum-classical network (PennyLane + PyTorch)."""
import numpy as np
import torch
from torch import nn
import matplotlib.pyplot as plt
import pennylane as qml
from sklearn.model_selection import train_test_split
from plots import save, moons, params, log_metrics

P = params(n_qubits=4, n_layers=2, epochs=30, lr=0.05, seed=0)
torch.manual_seed(P.seed)
N_QUBITS, N_LAYERS, EPOCHS = P.n_qubits, P.n_layers, P.epochs

X, y = moons(n=300, noise=0.2)
y = (y + 1) // 2                                   # {-1, +1} -> {0, 1} for cross-entropy
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=1)
to_t = lambda a, dt=torch.float32: torch.tensor(a, dtype=dt)
X_tr, X_te, y_tr, y_te = to_t(X_tr), to_t(X_te), to_t(y_tr, torch.long), to_t(y_te, torch.long)

dev = qml.device("default.qubit", wires=N_QUBITS)

@qml.qnode(dev, interface="torch")
def quantum_block(inputs, weights):                 # the argument MUST be called `inputs`
    qml.AngleEmbedding(inputs, wires=range(N_QUBITS))
    qml.BasicEntanglerLayers(weights, wires=range(N_QUBITS))
    return [qml.expval(qml.PauliZ(w)) for w in range(N_QUBITS)]

qlayer = qml.qnn.TorchLayer(quantum_block, {"weights": (N_LAYERS, N_QUBITS)})

hybrid = nn.Sequential(nn.Linear(2, N_QUBITS), nn.Tanh(),   # classical pre-processing
                       qlayer,                              # 4 qubits, 8 weights
                       nn.Linear(N_QUBITS, 2))              # classical read-out -> logits
classical = nn.Sequential(nn.Linear(2, N_QUBITS), nn.Tanh(),
                          nn.Linear(N_QUBITS, N_QUBITS), nn.Tanh(),
                          nn.Linear(N_QUBITS, 2))

def n_params(m):
    return sum(p.numel() for p in m.parameters())

def train(model, name):
    opt = torch.optim.Adam(model.parameters(), lr=P.lr)
    loss_fn = nn.CrossEntropyLoss()
    loader = torch.utils.data.DataLoader(list(zip(X_tr, y_tr)), batch_size=16, shuffle=True)
    hist = {"loss": [], "test": []}
    for epoch in range(EPOCHS):
        model.train()
        for xb, yb in loader:
            opt.zero_grad()
            loss = loss_fn(model(xb), yb)
            loss.backward()                      # gradients flow through the quantum layer
            opt.step()
        model.eval()
        with torch.no_grad():
            hist["loss"].append(loss_fn(model(X_tr), y_tr).item())
            hist["test"].append((model(X_te).argmax(1) == y_te).float().mean().item())
        print(f"{name:9s} epoch {epoch + 1:2d} loss {hist['loss'][-1]:.3f} test {hist['test'][-1]:.2f}")
    return hist

h_hyb, h_cls = train(hybrid, "hybrid"), train(classical, "classical")

fig, axes = plt.subplots(1, 2, figsize=(12, 4))
for h, lab in [(h_hyb, f"hybrid ({n_params(hybrid)} params)"),
               (h_cls, f"classical ({n_params(classical)} params)")]:
    axes[0].plot(h["loss"], label=lab)
    axes[1].plot(h["test"], label=lab)
axes[0].set_title("Training loss (cross-entropy)"); axes[0].set_xlabel("epoch"); axes[0].legend()
axes[1].set_title("Test accuracy"); axes[1].set_xlabel("epoch"); axes[1].set_ylim(0.4, 1.02)
axes[1].legend()
save(fig, "m07_hybrid")
log_metrics(hybrid_test_accuracy=h_hyb["test"][-1], classical_test_accuracy=h_cls["test"][-1],
            hybrid_params=n_params(hybrid), classical_params=n_params(classical))
