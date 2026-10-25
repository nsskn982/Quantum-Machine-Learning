# QAOA for MaxCut with learned initial angles

Solve MaxCut on small graphs; train a classical model to predict good starting angles.

## Goal

Cut the number of optimiser steps QAOA needs by predicting good initial angles from graph features.

## Builds on

Module 3, Module 5

## Open questions

- Which graph features (degree statistics, size, density) predict good angles?
- Do angles learned on 6-node graphs transfer to 10-node graphs?
- How does the approximation ratio scale with QAOA depth p?

## Ideas to try

- Build a data set of random graphs with optimised angles for p = 1, 2.
- Fit a small regressor from graph features to angles.
- Compare steps-to-converge from random vs predicted angles.

## Experiments

None yet. Add one with a script in `experiments/` and an `[[experiments]]` entry in `project.toml`, then run `python manage.py sync_projects`.

## Quality bar for results

- A classical baseline with a similar number of parameters
- At least 5 seeds, reported as mean ± standard deviation
- How results change with qubit count
- One run under a realistic noise model
