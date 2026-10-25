# Trainable quantum kernels

Tune feature-map angles to maximise kernel-target alignment, then compare with a fixed ZZ map.

## Goal

Learn a feature map whose kernel matches the labels, and measure how much that beats a fixed feature map.

## Builds on

Module 3, Module 6

## Open questions

- Does a higher kernel-target alignment actually give higher test accuracy?
- How many trainable parameters before the kernel overfits?
- Can alignment be trained on a subset of the data and still transfer?

## Ideas to try

- Use PennyLane's kernels module and a two-moons baseline first.
- Track alignment and test accuracy per training step as metrics.
- Try a data set with 4+ features (Iris, breast cancer).

## Experiments

None yet. Add one with a script in `experiments/` and an `[[experiments]]` entry in `project.toml`, then run `python manage.py sync_projects`.

## Quality bar for results

- A classical baseline with a similar number of parameters
- At least 5 seeds, reported as mean ± standard deviation
- How results change with qubit count
- One run under a realistic noise model
