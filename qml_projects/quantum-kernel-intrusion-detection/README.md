# Quantum-kernel intrusion detection

Quantum-kernel SVM on IoT traffic features after PCA (NSL-KDD or CIC-IoT), against an RBF SVM and an MLP.

## Goal

Find out whether a quantum kernel separates normal from malicious IoT traffic better than tuned classical kernels at the same feature count.

## Builds on

Module 4, Module 6

## Open questions

- Which 4–8 features (after PCA or feature selection) keep most of the attack signal?
- Does the quantum kernel help on rare attack classes, or only on easy ones?
- How does accuracy change as the kernel bandwidth (feature scaling) changes?

## Ideas to try

- Start binary (normal vs attack), then try one-vs-rest per attack type.
- Add kernel bandwidth as a parameter and sweep it.
- Compare inference cost with a TinyML-sized classical model.

## Experiments

None yet. Add one with a script in `experiments/` and an `[[experiments]]` entry in `project.toml`, then run `python manage.py sync_projects`.

## Quality bar for results

- A classical baseline with a similar number of parameters
- At least 5 seeds, reported as mean ± standard deviation
- How results change with qubit count
- One run under a realistic noise model
