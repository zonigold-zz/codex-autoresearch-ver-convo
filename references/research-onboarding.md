# Research Onboarding Protocol

Use this reference when the task is research-facing: datasets, training, evaluation, ablation, analysis, benchmarking, or manuscript support.

## Trigger conditions
Load this reference when any of the following is true:
- the user mentions dataset, experiment, metric, model training, benchmark, ablation, report, or manuscript
- the repo contains research signals such as `train*.py`, `eval*.py`, `configs/`, `notebooks/`, `data/`, or `datasets/`
- `research/project.yaml` already exists in the target repo

## First-run behavior
If `research/project.yaml` is missing in the target repo:
1. Ask a focused onboarding round that confirms:
   - research goal
   - paradigm
   - primary metric and direction
   - dataset path and split policy
   - safety or governance constraints
   - desired report artifacts
2. Propose defaults grounded in the repo.
3. Initialize or refresh:
   - `research/project.yaml`
   - `research/datasets.yaml`
   - `research/permissions.yaml`
4. Use `scripts/research_bootstrap.py --repo <target-repo>` to seed files when helpful.
5. Use `scripts/research_dataset_probe.py --repo <target-repo>` before asking detailed dataset questions when the data layout is unclear.

## Returning-run behavior
If research files already exist:
- read them before asking anything
- ask only for deltas
- do not re-ask stable defaults unless the repo or objective changed materially

## Research-specific confirmations
Prefer short multiple-choice prompts.
- What is the task family: classification, regression, forecasting, representation learning, causal analysis, or manuscript/report support?
- What is the split policy: subject-heldout, session-heldout, random split, k-fold, or external validation?
- Must raw data remain immutable?
- Which guards must never be violated?

## Output expectations
Before launch, summarize:
- confirmed goal
- confirmed metric and verify command
- dataset / split assumption
- guardrails
- requested artifacts

After launch, do not keep questioning during the active run.
