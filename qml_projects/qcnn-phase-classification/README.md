# QCNN for phase classification

Classify ground states of the transverse-field Ising model with a quantum convolutional network.

## Goal

Train a QCNN to tell ordered from disordered phases of the transverse-field Ising model directly from quantum states.

## Builds on

Module 5, Module 8

## Open questions

- How close to the critical point can the QCNN classify correctly?
- Does the QCNN avoid barren plateaus as the chain grows?
- How many training states are needed?

## Ideas to try

- Prepare ground states with exact diagonalisation for 4–8 spins.
- Plot predicted phase against field strength.
- Compare with a classical model on classical shadows of the same states.

## Experiments

None yet. Add one with a script in `experiments/` and an `[[experiments]]` entry in `project.toml`, then run `python manage.py sync_projects`.

## Quality bar for results

- A classical baseline with a similar number of parameters
- At least 5 seeds, reported as mean ± standard deviation
- How results change with qubit count
- One run under a realistic noise model
