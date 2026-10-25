# Re-uploading depth study on MNIST

Classify PCA-reduced digits (4-8 features); chart accuracy against layers and qubits.

## Goal

Map how accuracy depends on the number of re-uploading layers and qubits for a small digit classifier.

## Builds on

Module 5

## Open questions

- Where does adding layers stop helping on 4 PCA features?
- Is it better to spend the budget on qubits (features) or layers (depth)?
- How far is the best circuit from a logistic regression on the same features?

## Ideas to try

- Run the baseline experiment with n_layers = 1, 2, 4, 6 and compare test accuracy in the run table.
- Add a second experiment that sweeps n_qubits with layers fixed.
- Try harder digit pairs (3 vs 5, 4 vs 9).

## Experiments

- `baseline`: see `experiments/e01_baseline.py`.

## Quality bar for results

- A classical baseline with a similar number of parameters
- At least 5 seeds, reported as mean ± standard deviation
- How results change with qubit count
- One run under a realistic noise model
