# Research Reporting Protocol

When the task is research-facing, produce a human-readable summary in addition to the normal autoresearch artifacts.

## Default outputs
- `reports/latest_run.md`
- `reports/methods_draft.md` when the user asks for manuscript-ready language or experiment documentation

## Minimum contents for `reports/latest_run.md`
1. Objective
2. Metric and verification
3. Dataset and split assumptions
4. Guards and safety constraints
5. Best retained result
6. Key changes tried
7. Open blockers
8. Recommended next actions

## Writing rules
- Prefer compact, researcher-readable prose over raw internal fields.
- Derive claims from `research-results.tsv` metadata/rows and `autoresearch-state.json`; treat any prior report text only as a richness/style reference, not as source of truth.
- Mention uncertainty explicitly when verification is partial.
- Do not expose internal-only state details unless they help the user decide the next step.
