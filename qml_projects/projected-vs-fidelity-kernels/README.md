# Projected vs fidelity kernels

Measure how both kernel types concentrate as qubits grow from 2 to 12.

## Goal

Show, with numbers, how fast fidelity and projected kernels concentrate with qubit count, and when projected kernels stay useful.

## Builds on

Module 6, Module 8

## Open questions

- At which qubit count does the off-diagonal variance of each kernel drop below shot noise?
- Does feature scaling (bandwidth) delay concentration for both kernels equally?
- How do the results change with a hardware-efficient vs IQP feature map?

## Ideas to try

- Plot off-diagonal variance vs qubits on a log scale for both kernels.
- Add finite shots to see when the kernel becomes unmeasurable.
- Read Thanasilp et al. on exponential concentration first.

## Experiments

None yet. Add one with a script in `experiments/` and an `[[experiments]]` entry in `project.toml`, then run `python manage.py sync_projects`.

## Quality bar for results

- A classical baseline with a similar number of parameters
- At least 5 seeds, reported as mean ± standard deviation
- How results change with qubit count
- One run under a realistic noise model
