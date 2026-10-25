# Quantum autoencoder

Compress 3-qubit states into 2 qubits and measure reconstruction fidelity.

## Goal

Train a circuit that compresses a family of quantum states into fewer qubits and recovers them with high fidelity.

## Builds on

Module 2, Module 5

## Open questions

- Which state families compress well (GHZ-like, W-like, random)?
- How does fidelity fall when compressing further (3 to 1 qubit)?
- How sensitive is the trained encoder to noise?

## Ideas to try

- Start with the swap-test trash-state cost.
- Report fidelity per state family as metrics.
- Repeat under a depolarizing noise model.

## Experiments

None yet. Add one with a script in `experiments/` and an `[[experiments]]` entry in `project.toml`, then run `python manage.py sync_projects`.

## Quality bar for results

- A classical baseline with a similar number of parameters
- At least 5 seeds, reported as mean ± standard deviation
- How results change with qubit count
- One run under a realistic noise model
