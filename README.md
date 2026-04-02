<p align="center">
  <img src="image/banner.png" width="700" alt="Codex Autoresearch Convo">
</p>

# Codex Autoresearch Convo

Research-first, conversational autonomous research loops for Codex.

[Install](docs/INSTALL.md) · [Guide](docs/GUIDE.md) · [Examples](docs/EXAMPLES.md) · [Notice](NOTICE) · [License](LICENSE)

## What this variant is

Codex Autoresearch Convo keeps the autonomous loop core of stock `codex-autoresearch`:

**modify → verify → keep or discard → log → repeat**

What changes is the **research-facing user experience**.

Convo is designed for repositories where the hard part is not only running iterations, but also:

- deciding the task family and split policy cleanly
- remembering stable research assumptions
- avoiding repeated setup interviews
- keeping verify and guard commands explicit
- generating a short researcher-readable run summary

## What Convo changes compared with stock codex-autoresearch

| Area | Stock codex-autoresearch | Convo |
|---|---|---|
| First run | Setup is more generic and operator-driven | Repo scan + conversational onboarding + repo-grounded defaults |
| Later runs | Easy to restate the same assumptions | Reads repo-local research memory first and asks only for deltas |
| Research memory | Not the main UX abstraction | `research/project.yaml`, `research/datasets.yaml`, `research/permissions.yaml` are first-class |
| Guards | Easy to think of as one shell string | Repeated guards remain structured runtime items |
| Reporting | Core artifacts are strong, but the summary is more generic | `reports/latest_run.md` is treated as a researcher-readable output |
| Legacy repo adoption | Mixed memory shapes can persist | Includes a migration helper for legacy simple schema |

## Who this variant is for

Use Convo when you want Codex to act like a research assistant that remembers repo-local context such as:

- task family
- split policy
- metric and direction
- verify command
- guard commands
- raw-data mutability constraints
- desired report artifacts

This is especially useful for ML, neurotech, data-analysis, benchmarking, ablation, and manuscript-adjacent repositories where stable context matters across sessions.

## Quick start

1. Install this repository as the active repo-local skill for a target repo.
2. Open Codex in the target repo.
3. Invoke:

```text
$codex-autoresearch
Improve subject-heldout EEG classification quality without violating dataset integrity constraints.
```

4. On a first run, Convo:
   - scans the repo
   - proposes repo-grounded defaults
   - asks a short onboarding round
   - writes `research/*.yaml`
5. Choose a launch mode:
   - `foreground`
   - `background`
6. Launch with:
   - `foreground go`
   - or `background go`

Everything before `go` is setup.
Everything after `go` is autonomous execution.

## First-run onboarding

If canonical research memory is missing, Convo confirms the minimum durable facts:

- research goal
- task family
- primary metric and direction
- dataset path and split policy
- guardrails and mutation constraints
- desired report artifacts

The point is not to ask more questions than necessary.
The point is to avoid asking the same questions again later.

## Returning runs: delta-only

If canonical research memory already exists, Convo reads it before asking anything.

Returning-run behavior:

- reuse stable defaults from memory
- ask only for deltas
- do not re-ask the original onboarding questions unless the repo or objective changed materially

Typical delta-only questions include:

- “Keep the same split policy?”
- “Keep the same verify command?”
- “Add or remove guards?”
- “Continue the same objective, or switch metrics?”

## Canonical research memory

Convo uses three durable repo-local memory files:

- `research/project.yaml`
  - research goal, task family, objective, verify intent, guards, artifacts, notes
- `research/datasets.yaml`
  - dataset description, split assumptions, label source, mutability, known files
- `research/permissions.yaml`
  - write boundaries, guardrails, launch policy

Older repos may still contain flatter legacy YAML layouts.
Convo can read those, and this repository includes a migration helper for converting them into the canonical richer schema.

## Run artifacts

Convo distinguishes between two artifact groups.

### Research memory
- `research/project.yaml`
- `research/datasets.yaml`
- `research/permissions.yaml`

### Run state
- `research-results.tsv`
- `autoresearch-state.json`
- `autoresearch-lessons.md`
- `autoresearch-launch.json` (background only)
- `autoresearch-runtime.json` (background only)
- `autoresearch-runtime.log` (background only)

For research-facing repos, `scripts/research_report.py --repo <target-repo>` can synthesize `reports/latest_run.md` from artifact truth.

## Reporting

Convo treats the run summary as a real research artifact, not just a debugging convenience.

The report helper summarizes:

1. Objective
2. Metric and verification
3. Dataset and split assumptions
4. Guards and safety constraints
5. Best retained result
6. Key changes tried
7. Open blockers
8. Recommended next actions

## Repeated `--guard` usage

When launching helper-driven runs, prefer repeated `--guard` flags instead of composing one shell-specific command string.

```powershell
python .\.agents\skills\codex-autoresearch\scripts\autoresearch_runtime_ctl.py launch `
  --repo <target-repo> `
  --goal "Improve subject-heldout EEG classification quality without violating dataset integrity constraints." `
  --metric AUROC `
  --direction higher `
  --verify "python eval_eeg.py --config configs/experiment.yaml --metric-only" `
  --guard "python guard_dataset.py" `
  --guard "python train_eeg.py --config configs/experiment.yaml"
```

This keeps guard metadata structured in state, results logs, and downstream reports.

## Foreground and background

Convo uses one explicit launch boundary:

- **Before `go`**: interactive clarification, onboarding, confirmation
- **After `go`**: no more user questions during the active run

Use `foreground` when you want to supervise or smoke-test the loop.
Use `background` when you want a detached run and the target repo is configured for unattended operation.

## Windows notes

On Windows, pay attention to:

- repo-local symlink or junction installs for `.agents/skills/codex-autoresearch`
- trusted project behavior for project-scoped `.codex/config.toml`
- UTF-8 without BOM and LF line endings for Markdown, YAML, TOML, rules, and helper scripts

## Smoke-run snapshots

This repository includes smoke-run snapshots under `notes/smoke-runs/`.

They exist to show the full Convo pattern:

- repo scan
- first-run memory creation
- delta-only return behavior
- explicit verify and repeated guards
- artifact-backed reporting

## License and notice

This repository is distributed under the MIT License. See [LICENSE](LICENSE).

This repository is also a derivative work based on `leo-lilinxiao/codex-autoresearch`. See [NOTICE](NOTICE) for attribution and derivative-work context.
