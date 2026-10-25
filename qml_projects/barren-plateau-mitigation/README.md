# Barren-plateau mitigation

Compare layerwise training, identity-block initialisation and local costs.

## Goal

Compare mitigation strategies for barren plateaus by gradient variance and by final training loss.

## Builds on

Module 8

## Open questions

- Which strategy keeps gradient variance flat longest as qubits grow?
- Does a larger gradient at the start translate into a better final model?
- How do strategies combine (local cost + identity init)?

## Ideas to try

- Extend Module 8's script with an init_strategy parameter.
- Log gradient variance at 2–12 qubits per strategy.
- Train one small task to the end per strategy.

## Experiments

None yet. Add one with a script in `experiments/` and an `[[experiments]]` entry in `project.toml`, then run `python manage.py sync_projects`.

## Quality bar for results

- A classical baseline with a similar number of parameters
- At least 5 seeds, reported as mean ± standard deviation
- How results change with qubit count
- One run under a realistic noise model
