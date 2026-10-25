# Quantum reservoir computing for time series

Use a fixed random circuit as a reservoir and train only a linear read-out to forecast a signal.

## Goal

Test whether a fixed random quantum circuit is a useful reservoir for short-term forecasting, with only the linear read-out trained.

## Builds on

Module 2, Module 4

## Open questions

- How does forecast error depend on reservoir size and the number of measured observables?
- Does memory of past inputs fade too quickly?
- How does it compare with a classical echo-state network?

## Ideas to try

- Start with a sine wave plus noise, then a chaotic series (Mackey-Glass).
- Log test RMSE per configuration.
- Add measurement shot noise to see robustness.

## Experiments

None yet. Add one with a script in `experiments/` and an `[[experiments]]` entry in `project.toml`, then run `python manage.py sync_projects`.

## Quality bar for results

- A classical baseline with a similar number of parameters
- At least 5 seeds, reported as mean ± standard deviation
- How results change with qubit count
- One run under a realistic noise model
