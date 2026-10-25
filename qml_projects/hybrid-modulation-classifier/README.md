# Hybrid modulation classifier

Classify BPSK, QPSK and 16-QAM from synthetic I/Q samples at different SNR.

## Goal

Build a hybrid quantum-classical classifier for modulation types and compare it with a classical CNN across SNR levels.

## Builds on

Module 7

## Open questions

- At which SNR does each model break down?
- Which hand-crafted features (higher-order cumulants, amplitude statistics) suit a 4-qubit layer best?
- Does the quantum layer make the model more robust to noise, or less?

## Ideas to try

- Generate synthetic I/Q data with NumPy at SNR from -5 to 20 dB.
- Plot accuracy vs SNR for hybrid and classical.
- Add 8-PSK and 64-QAM once the three-class case works.

## Experiments

None yet. Add one with a script in `experiments/` and an `[[experiments]]` entry in `project.toml`, then run `python manage.py sync_projects`.

## Quality bar for results

- A classical baseline with a similar number of parameters
- At least 5 seeds, reported as mean ± standard deviation
- How results change with qubit count
- One run under a realistic noise model
