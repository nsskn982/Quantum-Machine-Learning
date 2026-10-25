"""Module 3: parameterised circuits, the parameter-shift rule, gradient descent."""
import numpy as np
import matplotlib.pyplot as plt
import pennylane as qml
from pennylane import numpy as pnp          # autograd-aware NumPy for trainable params
from plots import save

dev = qml.device("default.qubit", wires=1)

@qml.qnode(dev, diff_method="parameter-shift")
def f(theta):
    qml.RX(theta, wires=0)
    return qml.expval(qml.PauliZ(0))            # equals cos(theta)

# Three ways to get the derivative at one point
th = pnp.array(0.8, requires_grad=True)
auto = qml.grad(f)(th)
shift = (f(th + np.pi / 2) - f(th - np.pi / 2)) / 2   # parameter-shift rule
finite = (f(th + 1e-3) - f(th - 1e-3)) / 2e-3
print(f"qml.grad={auto:.5f}  shift={shift:.5f}  finite diff={finite:.5f}  exact={-np.sin(0.8):.5f}")

# Two-parameter circuit: cost landscape + gradient descent path
@qml.qnode(dev, diff_method="parameter-shift")
def cost(params):
    qml.RX(params[0], wires=0)
    qml.RY(params[1], wires=0)
    return qml.expval(qml.PauliZ(0))            # = cos(a) cos(b); minimum is -1

params = pnp.array([0.4, 0.3], requires_grad=True)
opt = qml.GradientDescentOptimizer(stepsize=0.4)
path, values = [params.copy()], [cost(params)]
for _ in range(30):
    params, c = opt.step_and_cost(cost, params)
    path.append(params.copy()); values.append(cost(params))
path = np.array(path)

thetas = np.linspace(-np.pi, np.pi, 200)
A, B = np.meshgrid(np.linspace(-0.5, np.pi + 0.5, 120), np.linspace(-0.5, np.pi + 0.5, 120))

fig, axes = plt.subplots(1, 3, figsize=(14, 4))
axes[0].plot(thetas, [f(t) for t in thetas], lw=2, label="f(θ) = ⟨Z⟩")
axes[0].plot(thetas, -np.sin(thetas), lw=2, ls="--", label="exact derivative")
pts = np.linspace(-np.pi, np.pi, 13)
axes[0].plot(pts, [(f(t + np.pi / 2) - f(t - np.pi / 2)) / 2 for t in pts], "o",
             label="parameter-shift estimate")
axes[0].set_xlabel("θ (rad)"); axes[0].set_title("Shift rule gives the exact gradient")
axes[0].legend(fontsize=8)

cs = axes[1].contourf(A, B, np.cos(A) * np.cos(B), levels=30, cmap="viridis")
fig.colorbar(cs, ax=axes[1], label="cost ⟨Z⟩")
axes[1].plot(path[:, 0], path[:, 1], "w.-", label="gradient descent")
axes[1].set_xlabel("a (RX angle)"); axes[1].set_ylabel("b (RY angle)")
axes[1].set_title("Cost landscape cos a · cos b"); axes[1].legend(fontsize=8)

axes[2].plot(values, "o-")
axes[2].axhline(-1, color="k", ls=":", label="global minimum")
axes[2].set_xlabel("step"); axes[2].set_ylabel("cost"); axes[2].set_title("Training curve")
axes[2].legend(fontsize=8)
save(fig, "m03_gradients")
