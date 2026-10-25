# Quantum transfer learning

Take ResNet-18 features from a small image set and feed them into a 4-qubit classifier head.

## Goal

Use a pretrained classical network as a feature extractor and test whether a small quantum head classifies as well as a classical head.

## Builds on

Module 7

## Open questions

- Does the quantum head match a linear head with the same number of parameters?
- How does performance change with 2, 4 and 6 qubits?
- How much does the feature reduction before the circuit matter?

## Ideas to try

- Follow the PennyLane quantum transfer learning demo.
- Use a small two-class image set.
- Log head-only parameter counts with the accuracy.

## Experiments

None yet. Add one with a script in `experiments/` and an `[[experiments]]` entry in `project.toml`, then run `python manage.py sync_projects`.

## Quality bar for results

- A classical baseline with a similar number of parameters
- At least 5 seeds, reported as mean ± standard deviation
- How results change with qubit count
- One run under a realistic noise model
