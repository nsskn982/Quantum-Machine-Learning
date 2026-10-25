"""Seed content for the eight modules, taken from the QML project plan."""

MODULES = [
    {
        "number": 1, "slug": "qubits-bloch-sphere", "title": "Qubits and the Bloch sphere",
        "week": "1", "tool": "Qiskit + PennyLane", "script": "m01_qubits.py", "figure": "m01_bloch.png",
        "summary": "A qubit is a unit vector; single-qubit gates are rotations of the Bloch sphere.",
        "concept": (
            "A qubit's state is a unit vector of two complex numbers, a and b. Measuring it gives 0 with "
            "probability |a|² and 1 with probability |b|². This is the Born rule.\n\n"
            "The angles θ and φ place the state as a point on the Bloch sphere. Single-qubit gates are "
            "rotations of that sphere: RY(θ) turns the arrow in the x–z plane, RX(θ) in the y–z plane. Every "
            "QML model later in this course is a stack of these rotations, with angles set by data or by "
            "trainable weights.\n\n"
            "The script builds the same circuit in Qiskit (a circuit object) and PennyLane (a Python function "
            "called a QNode) and checks that both give the same state."
        ),
        "formula": r"|\psi\rangle = \cos\tfrac{\theta}{2}|0\rangle + e^{i\varphi}\sin\tfrac{\theta}{2}|1\rangle",
        "figure_caption": "Left: the paths traced by RY and RX on the sphere. Right: P(0) follows cos²(θ/2).",
        "checkpoint": "Add qc.h(0) before the rotation. Predict where the RY path now starts, then run it and check.",
    },
    {
        "number": 2, "slug": "gates-entanglement", "title": "Gates, entanglement and measurement",
        "week": "2", "tool": "Qiskit", "script": "m02_entanglement.py", "figure": "m02_entanglement.png",
        "summary": "H and CNOT make a Bell state; shots turn amplitudes into counts.",
        "concept": (
            "Two qubits live in a 4-dimensional space with basis 00, 01, 10 and 11. A Hadamard puts one qubit "
            "into an equal superposition; a CNOT flips the second qubit only when the first is 1. Together "
            "they make the Bell state.\n\n"
            "The Bell state cannot be written as one qubit's state times the other's. That is entanglement: "
            "each qubit alone looks random, but the two always agree.\n\n"
            "Real hardware never shows amplitudes, only counts from repeated shots, so probabilities and "
            "expectation values such as ⟨Z⊗Z⟩ are estimated from samples."
        ),
        "formula": r"|\Phi^+\rangle = \tfrac{1}{\sqrt{2}}\left(|00\rangle + |11\rangle\right)",
        "figure_caption": "Histograms for a product state and a Bell state, and ⟨Z⊗Z⟩ as one qubit is rotated.",
        "checkpoint": "Build the state (|01⟩ + |10⟩)/√2 by adding one gate, and confirm its histogram.",
    },
    {
        "number": 3, "slug": "gradients-parameter-shift", "title": "Parameterised circuits and gradients",
        "week": "3", "tool": "PennyLane", "script": "m03_gradients.py", "figure": "m03_gradients.png",
        "summary": "The parameter-shift rule gives exact gradients from two extra circuit runs.",
        "concept": (
            "A parameterised quantum circuit has rotation angles you can tune. Its output, an expectation "
            "value, is a smooth function of those angles, so it can be trained with gradient descent.\n\n"
            "Real hardware cannot backpropagate. The parameter-shift rule solves this: for rotation gates, "
            "the exact derivative comes from running the same circuit with the angle shifted by ±π/2. It is "
            "exact, unlike finite differences, but costs two runs per parameter per step."
        ),
        "formula": r"\frac{\partial f}{\partial \theta} = \frac{f(\theta + \pi/2) - f(\theta - \pi/2)}{2}",
        "figure_caption": "Shift-rule estimates on the true derivative, a descent path on the cost surface, the training curve.",
        "checkpoint": "Swap qml.RX for qml.Hadamard in f. Why does qml.grad now complain?",
    },
    {
        "number": 4, "slug": "data-encoding", "title": "Data encoding (feature maps)",
        "week": "4", "tool": "PennyLane", "script": "m04_encoding.py", "figure": "m04_encoding.png",
        "summary": "How classical data becomes a quantum state, and why the choice matters.",
        "concept": (
            "Before a quantum model can learn, each data point x must become a state |ψ(x)⟩. This feature map "
            "matters more than the trainable part: the model can only separate what the encoding has already "
            "pulled apart.\n\n"
            "Angle encoding uses each feature as a rotation angle (d qubits for d features). Amplitude "
            "encoding loads x/‖x‖ as amplitudes (log₂ d qubits) but loses the norm. ZZ or IQP maps add "
            "entangling terms built from products of features.\n\n"
            "The fidelity between two encoded points measures how similar the model thinks they are. It is "
            "exactly the quantum kernel used in Module 6."
        ),
        "formula": r"k(x, x') = |\langle \psi(x) | \psi(x') \rangle|^2",
        "figure_caption": "Two moons as raw data, under angle encoding, and under amplitude encoding.",
        "checkpoint": "Scale the features to [0, 2π] instead of [0, π]. What happens to the angle-encoded classes, and why?",
    },
    {
        "number": 5, "params": {"n_layers": 3, "epochs": 40, "batch": 25, "stepsize": 0.1, "seed": 0}, "slug": "variational-classifier", "title": "Variational quantum classifier",
        "week": "5-6", "tool": "PennyLane", "script": "m05_vqc.py", "figure": "m05_vqc.png",
        "summary": "Encode, apply a trainable circuit, measure, and let a classical optimiser update the weights.",
        "concept": (
            "A variational quantum classifier encodes x, processes it with a trainable circuit U(w) of "
            "rotations and CNOTs (the ansatz), and reads out ⟨Z₀⟩ plus a bias. The sign is the class.\n\n"
            "A classical optimiser such as Adam updates w and b with gradients from Module 3. Only the circuit "
            "runs on quantum hardware; everything else is ordinary Python.\n\n"
            "Data re-uploading matters: encoding x again before every trainable layer lets even two qubits "
            "draw curved decision boundaries."
        ),
        "formula": r"f(x; w, b) = \langle \psi(x) | U(w)^\dagger Z_0 U(w) | \psi(x) \rangle + b",
        "figure_caption": "Loss and accuracy per epoch, and the decision boundary with test points.",
        "checkpoint": "Set N_LAYERS = 1 and rerun. Compare the boundary with 3 layers.",
    },
    {
        "number": 6, "params": {"reps": 2, "rbf_gamma": 1.0}, "slug": "quantum-kernels", "title": "Quantum kernels and the quantum SVM",
        "week": "7", "tool": "Qiskit ML", "script": "m06_kernels.py", "figure": "m06_kernels.png",
        "summary": "The quantum computer estimates a similarity matrix; a classical SVM does the training.",
        "concept": (
            "A support vector machine needs only a kernel: a similarity score for every pair of points. A "
            "quantum kernel uses the fidelity between encoded states as that score.\n\n"
            "The quantum computer only estimates the kernel matrix; training is a convex classical problem "
            "with no barren plateaus. That makes kernels the most reliable QML method to start with.\n\n"
            "A kernel helps only if same-class points come out more similar than different-class points. "
            "Always compare against a classical RBF kernel."
        ),
        "formula": r"K_{ij} = |\langle \psi(x_i) | \psi(x_j) \rangle|^2",
        "figure_caption": "ZZ quantum kernel and RBF kernel sorted by class, and the spread of kernel values.",
        "checkpoint": "Try reps=1 and reps=4 in the feature map and watch the off-diagonal values.",
    },
    {
        "number": 7, "params": {"n_qubits": 4, "n_layers": 2, "epochs": 30, "lr": 0.05, "seed": 0}, "slug": "hybrid-model", "title": "Hybrid quantum-classical model",
        "week": "8", "tool": "PennyLane + PyTorch", "script": "m07_hybrid.py", "figure": "m07_hybrid.png",
        "summary": "A quantum layer inside a PyTorch network, trained end to end against a classical baseline.",
        "concept": (
            "In practice a circuit is one layer inside a larger model: classical layers, a quantum layer, then "
            "more classical layers. PennyLane supplies the quantum layer's gradients, so loss.backward() works "
            "end to end.\n\n"
            "The layer before the circuit learns which angles to feed in; the layer after it learns how to "
            "combine the measurements.\n\n"
            "The honest question is whether the quantum layer beats a classical layer with a similar number "
            "of parameters, so the script trains both."
        ),
        "formula": "",
        "figure_caption": "Loss and test accuracy for the hybrid and the classical network.",
        "checkpoint": "Replace BasicEntanglerLayers with StronglyEntanglingLayers. Does test accuracy change, or only training time?",
    },
    {
        "number": 8, "params": {"layers": 10, "samples": 100, "max_qubits": 10, "seed": 0}, "slug": "noise-barren-plateaus", "title": "Noise, barren plateaus and honest benchmarking",
        "week": "9", "tool": "PennyLane + Qiskit Aer", "script": "m08_noise.py", "figure": "m08_noise.png",
        "summary": "Why gradients vanish as qubits are added, and how noise erases the signal.",
        "concept": (
            "Barren plateaus: for deep, randomly initialised circuits the gradient's variance shrinks "
            "exponentially with the number of qubits. The landscape is flat almost everywhere. Global costs "
            "suffer most; local costs, shallow circuits and careful initialisation help.\n\n"
            "Noise: a depolarizing channel replaces the state with random noise with probability p, and every "
            "noisy gate shrinks expectation values toward zero. Deeper circuits lose more signal.\n\n"
            "Rules for honest QML: compare with a classical baseline, report scaling with qubit count, and "
            "test under a realistic noise model."
        ),
        "formula": r"\mathrm{Var}\left[\partial_\theta C\right] \in O\left(b^{-n}\right), \quad b > 1",
        "figure_caption": "Gradient variance against qubit count (log scale), and ⟨Z⊗Z⟩ decaying with noisy depth.",
        "checkpoint": "Set LAYERS = 2 and rerun Part A. Explain the result using the light cone of Z₀.",
    },
]
