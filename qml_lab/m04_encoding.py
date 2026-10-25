"""Module 4: how classical data becomes a quantum state (feature maps)."""
import numpy as np
import matplotlib.pyplot as plt
import pennylane as qml
from plots import save, bloch_vector, draw_sphere, moons

X, y = moons(n=200)
dev = qml.device("default.qubit", wires=1)

@qml.qnode(dev)
def angle_encode(x):
    qml.RY(x[0], wires=0)       # feature 1 sets the polar angle
    qml.RZ(x[1], wires=0)       # feature 2 sets the azimuth
    return qml.state()

@qml.qnode(dev)
def amplitude_encode(x):
    qml.AmplitudeEmbedding(x, wires=0, normalize=True)   # x / |x| becomes [a, b]
    return qml.state()

angle_pts = np.array([bloch_vector(angle_encode(x)) for x in X])
amp_pts = np.array([bloch_vector(amplitude_encode(x + 0.05)) for x in X])  # +0.05 avoids x = 0

fig = plt.figure(figsize=(14, 4.5))
ax0 = fig.add_subplot(1, 3, 1)
ax0.scatter(X[:, 0], X[:, 1], c=y, cmap="coolwarm", s=12)
ax0.set_xlabel("x1 (scaled to [0, π])"); ax0.set_ylabel("x2")
ax0.set_title("Raw data: two moons")

for i, (pts, title) in enumerate([(angle_pts, "Angle encoding RY(x1) RZ(x2)"),
                                  (amp_pts, "Amplitude encoding x/|x|")]):
    ax = fig.add_subplot(1, 3, i + 2, projection="3d")
    draw_sphere(ax)
    ax.scatter(*pts.T, c=y, cmap="coolwarm", s=12, depthshade=False)
    ax.set_title(title)
save(fig, "m04_encoding")

# How far apart do two points end up? Fidelity |<psi(x)|psi(x')>|^2
def fidelity(enc, a, b):
    return abs(np.vdot(enc(a), enc(b))) ** 2
i, j = np.argmax(y == 1), np.argmax(y == -1)
print("angle fidelity between classes:", round(fidelity(angle_encode, X[i], X[j]), 3))
print("amplitude fidelity between classes:", round(fidelity(amplitude_encode, X[i] + .05, X[j] + .05), 3))
