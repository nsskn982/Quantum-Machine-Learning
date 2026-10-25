# Simulator vs IBM hardware benchmark

Run your best small model on a real IBM backend and report the accuracy gap and its sources.

## Goal

Measure the gap between simulated and real-hardware results for one small model, and explain where it comes from.

## Builds on

Module 2, Module 8

## Open questions

- How large is the accuracy gap, and how much is readout vs gate error?
- Does transpiling for the device's layout change the gap?
- How stable are results from one day to the next?

## Ideas to try

- Use the IBM Quantum Platform free plan and a 2–4 qubit model.
- Record backend name, date and calibration with every result.
- Compare with Aer using the device's noise model.

## Experiments

None yet. Add one with a script in `experiments/` and an `[[experiments]]` entry in `project.toml`, then run `python manage.py sync_projects`.

## Quality bar for results

- A classical baseline with a similar number of parameters
- At least 5 seeds, reported as mean ± standard deviation
- How results change with qubit count
- One run under a realistic noise model
