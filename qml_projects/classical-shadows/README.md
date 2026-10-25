# Learning from classical shadows

Predict state properties from randomised measurements and compare with full tomography.

## Goal

Measure how few randomised measurements are needed to estimate observables and entanglement, compared with full tomography.

## Builds on

Module 2, Module 8

## Open questions

- How does estimation error scale with the number of snapshots?
- Which observables are cheap to estimate and which are not?
- Can a classical model trained on shadows predict a phase label?

## Ideas to try

- Use PennyLane's classical_shadow measurement.
- Plot error vs number of snapshots on log axes.
- Link to the QCNN project for a shared data set.

## Experiments

None yet. Add one with a script in `experiments/` and an `[[experiments]]` entry in `project.toml`, then run `python manage.py sync_projects`.

## Quality bar for results

- A classical baseline with a similar number of parameters
- At least 5 seeds, reported as mean ± standard deviation
- How results change with qubit count
- One run under a realistic noise model
