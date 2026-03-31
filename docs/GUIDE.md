# Operator's Manual

This guide documents the Convo variant's operator flow. It assumes the shared codex-autoresearch loop core remains intact and focuses on what is different in the user-facing experience.

---

## Convo vs Stock

Stock codex-autoresearch is already interactive before launch and autonomous after launch. Convo adds a research-specific conversational layer on top of that:

- richer first-run onboarding for research repos
- persistent canonical research memory
- delta-only questions on returning runs
- explicit documentation for foreground/background `go`
- built-in examples grounded in the repo's research regression fixture

The loop itself is still baseline -> edit -> verify -> guard -> keep or discard -> record.

## Interaction Model

Convo still has two phases.

### Phase 1: Setup

Before `go`, Codex may:

- inspect the repo
- read existing research memory
- ask onboarding questions
- propose defaults
- confirm verify and guard commands
- ask you to choose `foreground` or `background`

### Phase 2: Execution

After `go`, the active run is autonomous:

- no more setup questions
- no mid-run clarification prompts
- ambiguities are handled using best judgment and the saved protocol

That `go` boundary is the main behavioral contract for this variant.

## First-Run Onboarding Flow

When canonical research memory is absent, Convo performs a focused onboarding round. The goal is to capture the minimum durable facts needed for later delta-only runs.

Convo confirms:

- research goal
- task family
- primary metric and direction
- dataset location and split policy
- data mutation rules
- guardrails and desired reports

Then it initializes or refreshes:

- `project.yaml`
- `datasets.yaml`
- `permissions.yaml`

Canonical richer schema for new writes:

- `project.yaml`
  - `goal`
  - `task_family`
  - `primary_repo`
  - `scope`
  - `objective`
  - `split_policy`
  - `verify`
  - `guards`
  - `artifacts`
  - `notes`
- `datasets.yaml`
  - `datasets[].name`
  - `datasets[].path`
  - `datasets[].role`
  - `datasets[].modality`
  - `datasets[].label_source`
  - `datasets[].label_unit`
  - `datasets[].target_type`
  - `datasets[].split_policy`
  - `datasets[].raw_data_mutability`
  - `datasets[].known_files`
  - `datasets[].schema`
  - `datasets[].assumptions`
- `permissions.yaml`
  - `permissions`
  - `guardrails`
  - `launch_policy`

Some repos store those files under `research/`; some keep them at repo root. This codebase supports both, and `scripts/research_migrate_schema.py` exists to migrate legacy shapes into the richer schema.

## Returning-Run Delta-Only Flow

When research memory already exists, Convo reads it first and narrows the conversation to changes only.

What stays stable by default:

- task family
- split policy
- existing verify command
- existing guard commands
- report targets
- launch policy

What Convo asks only if needed:

- whether the objective changed
- whether a new guard is required
- whether the split policy changed
- whether the run should be foreground or background this time

This avoids re-collecting stable facts on every invocation.

## Canonical Files and Purpose

### Research memory

- `project.yaml`: durable statement of the objective and verification contract
- `datasets.yaml`: durable dataset inventory and integrity assumptions
- `permissions.yaml`: durable operator guardrails and launch policy

### Run memory

- `research-results.tsv`: append-only main audit log for baseline and iterations
- `autoresearch-state.json`: compact retained state for resume and reports
- `autoresearch-lessons.md`: strategy memory carried across runs

### Background-only runtime control

- `autoresearch-launch.json`: confirmed launch manifest
- `autoresearch-runtime.json`: detached runtime status, PID, terminal reason
- `autoresearch-runtime.log`: detached runtime logging

### Derived reporting

- `reports/latest_run.md`: researcher-readable report synthesized from `research-results.tsv` and `autoresearch-state.json`

## Foreground and Background Behavior

Convo shares the same loop protocol in both modes. The difference is execution location and control files.

### Foreground

- launched after you answer the setup questions and reply `go`
- the loop continues in the current Codex session
- creates run memory files
- does not create launch/runtime control files
- stop by interrupting the active session

### Background

- launched after you answer the setup questions and reply `go`
- writes `autoresearch-launch.json`
- starts the detached runtime controller
- creates launch/runtime control files in the primary repo
- `status` and `stop` operate through the runtime controller

Foreground and background are mutually exclusive for the same primary repo artifacts at the same time.

## EEG Regression Smoke Run

Use the current regression fixture as the reference example:

- Results log: [research-results.tsv](F:\repos\codex-autoresearch-ver-convo\notes\smoke-runs\2026-03-31-regression-rerun\regression-lab\research-results.tsv)
- State snapshot: [autoresearch-state.json](F:\repos\codex-autoresearch-ver-convo\notes\smoke-runs\2026-03-31-regression-rerun\regression-lab\autoresearch-state.json)

Fixture summary:

- Goal: improve subject-heldout EEG classification quality without violating dataset integrity constraints
- Session mode: `foreground`
- Verify: `python eval_eeg.py --config configs/experiment.yaml --metric-only`
- Guards:
  - `python guard_dataset.py`
  - `python train_eeg.py --config configs/experiment.yaml`
- Baseline AUROC: `0.75`
- Best retained AUROC: `1.0`

The retained keep in that fixture rewired score assignments into `configs/experiment.yaml` and made `eval_eeg.py` consume the config-defined subject-heldout scores.

## Repeated `--guard` for Multi-Guard Launches

When launching through helper scripts, prefer repeated `--guard` flags:

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

Do not collapse multi-guard launches into a shell-specific `&&` string unless you are intentionally using a single composite guard. Repeated `--guard` keeps each safety check first-class in state, TSV metadata, and generated reports.

## Windows Notes

### Repo-local skill symlink

For live development on Windows, prefer a repo-local symlink or junction for `.agents/skills/codex-autoresearch` instead of copying the skill each time.

Typical PowerShell flow:

```powershell
New-Item -ItemType SymbolicLink `
  -Path .agents\skills\codex-autoresearch `
  -Target F:\repos\codex-autoresearch-ver-convo
```

If symlink creation is restricted, use a junction.

### Trusted project configuration

Background runs work best when the project is treated as trusted and Codex will not stop for approval on every `git commit` or rollback step. Use a stricter sandbox only when you explicitly want that friction.

### BOM and LF precautions

- Prefer UTF-8 without BOM for Markdown and YAML.
- Preserve LF line endings for cross-platform consistency.
- Be careful with Windows editors that silently introduce BOM or CRLF.
- If a file already has a specific encoding/line-ending convention, keep it consistent unless you are intentionally normalizing it.

## Reporting and Migration Helpers

Useful commands:

```bash
python scripts/research_migrate_schema.py --repo F:\lab\convo-skill-regression-lab --dry-run
python scripts/research_report.py --repo F:\lab\convo-skill-regression-lab
```

Use migration when a repo still has the legacy flat research YAMLs. Use reporting when a run already produced canonical run memory and you want a compact researcher-facing summary.

## Minimal Operator Rules

- On first run, confirm stable research facts and initialize memory.
- On returning runs, ask only for deltas.
- Treat `go` as the hard launch boundary.
- Record every completed experiment before the next one starts.
- Prefer repeated `--guard` for multi-guard helper launches.
- Keep Windows encoding and line-ending handling explicit.
