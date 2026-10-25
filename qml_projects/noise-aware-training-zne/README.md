# Noise-aware training with error mitigation

Train a VQC under Aer noise and apply zero-noise extrapolation.

## Goal

Quantify how much zero-noise extrapolation recovers the accuracy of a variational classifier trained and tested under realistic noise.

## Builds on

Module 5, Module 8

## Open questions

- Is it better to train with noise or train noise-free and mitigate at test time?
- How much does mitigation cost in extra circuit runs?
- Which noise model (device-based vs simple depolarizing) changes the conclusion?

## Ideas to try

- Use a fake IBM backend noise model in Aer.
- Log accuracy without, with ZNE, and noise-free.
- Try readout-error mitigation separately.

## Experiments

None yet. Add one with a script in `experiments/` and an `[[experiments]]` entry in `project.toml`, then run `python manage.py sync_projects`.

## Quality bar for results

- A classical baseline with a similar number of parameters
- At least 5 seeds, reported as mean ± standard deviation
- How results change with qubit count
- One run under a realistic noise model
