# Research Reporting Protocol

When the task is research-facing, produce a human-readable summary in addition to the normal autoresearch artifacts.

## Default outputs
- `reports/latest_run.md`
- `reports/methods_draft.md` when the user asks for manuscript-ready language or experiment documentation

## Minimum contents for `reports/latest_run.md`
1. Objective
2. Confirmed metric and verify command
3. Dataset / split assumptions
4. Guards and safety constraints
5. Best retained result so far
6. Key changes tried
7. Open blockers
8. Recommended next actions

## Writing rules
- Prefer compact, researcher-readable prose over raw internal fields.
- Mention uncertainty explicitly when verification is partial.
- Do not expose internal-only state details unless they help the user decide the next step.
