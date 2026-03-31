<p align="center">
  <img src="image/banner.png" width="700" alt="Codex Autoresearch Convo">
</p>

<h2 align="center"><b>Codex Autoresearch Convo</b></h2>

<p align="center">
  <i>Conversational autonomous research loops for Codex.</i>
</p>

<p align="center">
  <a href="docs/INSTALL.md">Install</a> |
  <a href="docs/GUIDE.md">Guide</a> |
  <a href="docs/EXAMPLES.md">Examples</a>
</p>

---

## What This Variant Changes

Convo keeps the shared codex-autoresearch loop core, but changes the user-facing flow for research work:

- The setup phase is more conversational and researcher-oriented than stock codex-autoresearch.
- First runs initialize canonical research memory files so later runs do not have to restate stable facts.
- Returning runs read that memory first and ask only for deltas.
- Foreground and background still share the same loop core, but the docs now treat `go` as the canonical launch boundary.
- Research reporting and memory migration are first-class workflows in this variant.

Compared with stock codex-autoresearch, the loop semantics are intentionally familiar. The main difference is how the skill onboards a repo, persists research context, and resumes without re-interviewing the user every time.

## Quick Start

1. Install the skill into the target repo. See [docs/INSTALL.md](docs/INSTALL.md).
2. Open Codex in that repo and invoke:

```text
$codex-autoresearch
Improve subject-heldout EEG classification quality without violating dataset integrity constraints.
```

3. On a first run, Convo asks a short onboarding round, proposes defaults grounded in the repo, and writes canonical research memory files.
4. Choose `foreground` or `background`.
5. Reply `go`.

Everything before `go` is setup. Everything after `go` is autonomous execution.

## First-Run Onboarding

If canonical research memory is missing, Convo treats the repo as a first run and confirms the minimum durable facts:

- research goal
- task family
- primary metric and direction
- dataset path and split policy
- guardrails and mutation constraints
- desired report artifacts

It then initializes the canonical research memory files:

- `project.yaml`: high-level research objective, scope, metric intent, verify command, artifacts, notes
- `datasets.yaml`: dataset inventory, split policy, label source, mutability, assumptions
- `permissions.yaml`: allowed write surfaces, guardrails, launch policy

Some repos keep those files at repo root; others place them under `research/`. This variant supports both layouts and documents the canonical richer schema for new writes.

## Returning Runs: Delta-Only

If the research memory files already exist, Convo reads them before asking anything. The returning-run rule is simple:

- reuse stable defaults from memory
- ask only for deltas
- do not re-ask the original onboarding questions unless the objective or repo changed materially

Typical delta-only questions:

- "Same subject-heldout split, or has the evaluation policy changed?"
- "Keep the same guards, or add a new smoke check?"
- "Are we continuing the same objective or switching to a new metric?"

## Canonical Memory and Run Artifacts

Convo has two distinct artifact groups.

Research memory:

- `project.yaml`: durable research objective and verification intent
- `datasets.yaml`: durable dataset description and split assumptions
- `permissions.yaml`: durable guardrails, write permissions, and launch policy

Run state:

- `research-results.tsv`: full per-iteration audit log
- `autoresearch-state.json`: compact retained state for resume/reporting
- `autoresearch-lessons.md`: cross-run lesson memory
- `autoresearch-launch.json`: confirmed background launch manifest only
- `autoresearch-runtime.json`: detached runtime control state only
- `autoresearch-runtime.log`: detached runtime log only

For research-facing repos, `scripts/research_report.py --repo <repo>` synthesizes `reports/latest_run.md` from `research-results.tsv` and `autoresearch-state.json`.

## Foreground and Background `go`

Convo uses one explicit launch boundary:

- Before `go`: interactive clarification, onboarding, run-mode choice
- After `go`: no more user questions during the active run

Run modes differ only in where the loop executes:

- `foreground`: the current Codex session runs the loop; no launch/runtime control files are created
- `background`: the detached runtime controller is launched; `autoresearch-launch.json`, `autoresearch-runtime.json`, and `autoresearch-runtime.log` are created in the primary repo

Status and stop are background-only runtime controls. Foreground is controlled by the active session itself.

## EEG Smoke-Run Example

The current regression fixture in [notes/smoke-runs/2026-03-31-regression-rerun/regression-lab/research-results.tsv](F:\repos\codex-autoresearch-ver-convo\notes\smoke-runs\2026-03-31-regression-rerun\regression-lab\research-results.tsv) shows the Convo flow on a subject-heldout EEG example:

- Goal: improve subject-heldout EEG classification quality without violating dataset integrity constraints
- Verify: `python eval_eeg.py --config configs/experiment.yaml --metric-only`
- Guards:
  - `python guard_dataset.py`
  - `python train_eeg.py --config configs/experiment.yaml`
- Baseline AUROC: `0.75`
- Retained best AUROC: `1.0`

That fixture is the canonical smoke-run example for this variant because it exercises:

- research-memory-aware setup
- repeated guards
- a researcher-readable goal
- report generation from run artifacts

## Repeated `--guard` Usage

For multi-guard launches, prefer repeating `--guard` instead of composing one shell-specific string:

```bash
python .agents/skills/codex-autoresearch/scripts/autoresearch_runtime_ctl.py launch \
  --repo F:\lab\convo-skill-regression-lab \
  --goal "Improve subject-heldout EEG classification quality without violating dataset integrity constraints." \
  --metric AUROC \
  --direction higher \
  --verify "python eval_eeg.py --config configs/experiment.yaml --metric-only" \
  --guard "python guard_dataset.py" \
  --guard "python train_eeg.py --config configs/experiment.yaml"
```

This preserves each guard as a first-class item in state and metadata while remaining backward-compatible with single-guard runs.

## Windows Notes

- Repo-local skill install: on Windows, use a repo-local symlink or junction for `.agents/skills/codex-autoresearch` when you want live edits.
- Trusted project config: if you want unattended background runs, configure Codex for a trusted project so approvals do not interrupt `git commit` or rollback operations.
- BOM and LF: write docs/YAML in UTF-8 without BOM when possible, and preserve LF line endings. Be careful with editors that silently add BOM or CRLF, especially for Markdown and YAML consumed across platforms.

## Validation and Reporting

Relevant local checks:

- `python scripts/research_migrate_schema.py --repo <repo> --dry-run`
- `python scripts/research_report.py --repo <repo>`
- `bash scripts/run_skill_e2e.sh interactive-smoke`
- `bash scripts/run_skill_e2e.sh runtime-smoke --clean`
- `bash scripts/run_skill_e2e.sh exec-smoke --clean`

## Project Layout

Key files for this variant:

- [docs/INSTALL.md](F:\repos\codex-autoresearch-ver-convo\docs\INSTALL.md)
- [docs/GUIDE.md](F:\repos\codex-autoresearch-ver-convo\docs\GUIDE.md)
- [docs/EXAMPLES.md](F:\repos\codex-autoresearch-ver-convo\docs\EXAMPLES.md)
- [agents/openai.yaml](F:\repos\codex-autoresearch-ver-convo\agents\openai.yaml)
- [references/research-onboarding.md](F:\repos\codex-autoresearch-ver-convo\references\research-onboarding.md)

## License

MIT. See [LICENSE](LICENSE).
