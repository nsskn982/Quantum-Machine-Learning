# Quantum reinforcement learning on CartPole

Use a variational circuit as the policy network in a REINFORCE agent.

## Goal

Train a variational quantum policy that balances CartPole and compare sample efficiency with a small classical policy.

## Builds on

Module 5, Module 7

## Open questions

- How many episodes does the quantum policy need compared with a classical one?
- Does input scaling or data re-uploading matter most for policy quality?
- How sensitive is learning to the number of layers?

## Ideas to try

- Use 4 qubits for the 4 CartPole observations.
- Log the average reward over the last 20 episodes as a metric.
- Read Jerbi et al. on parametrized quantum policies.

## Experiments

None yet. Add one with a script in `experiments/` and an `[[experiments]]` entry in `project.toml`, then run `python manage.py sync_projects`.

## Quality bar for results

- A classical baseline with a similar number of parameters
- At least 5 seeds, reported as mean ± standard deviation
- How results change with qubit count
- One run under a realistic noise model
