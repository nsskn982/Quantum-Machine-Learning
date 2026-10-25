# Quantum GAN for a 1-D distribution

Train a quantum generator to sample a log-normal distribution against a classical discriminator.

## Goal

Learn a target 1-D distribution with a quantum generator and compare its quality with a classical generator of similar size.

## Builds on

Module 5, Module 7

## Open questions

- How many qubits (bins) are needed for a useful approximation?
- Is training stable, or does it oscillate like classical GANs?
- What is the KL divergence against a small classical GAN?

## Ideas to try

- Use 3 qubits (8 bins) and a log-normal target first.
- Log KL divergence per epoch as a metric.
- Try a bimodal target to test mode collapse.

## Experiments

None yet. Add one with a script in `experiments/` and an `[[experiments]]` entry in `project.toml`, then run `python manage.py sync_projects`.

## Quality bar for results

- A classical baseline with a similar number of parameters
- At least 5 seeds, reported as mean ± standard deviation
- How results change with qubit count
- One run under a realistic noise model
