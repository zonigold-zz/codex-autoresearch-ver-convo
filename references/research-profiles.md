# Research Profiles

Use these defaults only as starting points. Always ground them in the repo and let the user confirm or correct.

## Classification
- Typical metric: AUROC, accuracy, balanced accuracy, F1
- Typical guards: schema validation, leakage check, smoke test
- Common question: is the split subject-heldout or random?

## Regression
- Typical metric: MAE, RMSE, R^2
- Typical guards: unit consistency, missing-value check, smoke test

## Forecasting
- Typical metric: sMAPE, MAE, RMSE
- Typical guards: time leakage check, window definition, backtest smoke test

## Representation learning
- Typical metric: linear probe score, retrieval score, contrastive loss proxy
- Typical guards: embedding shape check, downstream probe reproducibility

## Causal / intervention analysis
- Typical metric: effect estimate stability, calibration, error on held-out cohorts
- Typical guards: cohort definition, covariate balance, leakage prohibition

## Manuscript / reporting support
- Typical outputs: methods draft, result summary, figure checklist
- Keep code changes minimal unless the user explicitly asks for pipeline changes

## Default artifact policy
For research-facing tasks, prefer these human-readable outputs when they are useful:
- `reports/latest_run.md`
- `reports/methods_draft.md`
