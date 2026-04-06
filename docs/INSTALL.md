# Installation

This page covers installation and local-development notes for the **Convo** variant.

## Recommended layout

For this variant, prefer a **repo-local install** so the skill and its research-specific docs travel with the target repo.

```text
PATH_TO_TARGET_REPO/
  .agents/
    skills/
      codex-autoresearch -> PATH_TO_LOCAL_CLONE_OF_CODEX_AUTORESEARCH_VER_CONVO
```

This keeps Convo active only where you want its research-memory behavior.

## Install options

### 1. Repo-local symlink or junction (recommended for development)

Clone this repository somewhere on your machine:

```powershell
git clone https://github.com/zonigold-zz/codex-autoresearch-ver-convo.git
```

Inside the target repo, create a repo-local skill link.

PowerShell symbolic link:

```powershell
New-Item -ItemType SymbolicLink `
  -Path PATH_TO_TARGET_REPO\.agents\skills\codex-autoresearch `
  -Target PATH_TO_LOCAL_CLONE_OF_CODEX_AUTORESEARCH_VER_CONVO
```

If Windows symlinks are unavailable, use a junction:

```powershell
cmd /c mklink /J PATH_TO_TARGET_REPO\.agents\skills\codex-autoresearch PATH_TO_LOCAL_CLONE_OF_CODEX_AUTORESEARCH_VER_CONVO
```

### 2. Copy install

Use this if you do not want a live link.

```powershell
git clone https://github.com/zonigold-zz/codex-autoresearch-ver-convo.git
Copy-Item -Recurse PATH_TO_LOCAL_CLONE_OF_CODEX_AUTORESEARCH_VER_CONVO PATH_TO_TARGET_REPO\.agents\skills\codex-autoresearch
```

### 3. Skill installer

If you use a skill installer workflow, point it at this repository, not the upstream stock repo.

```text
$skill-installer install https://github.com/zonigold-zz/codex-autoresearch-ver-convo
```

Restart Codex after install changes.

## Verify the install

Open Codex in the target repo and check:

1. Type `$`
2. Confirm `codex-autoresearch` appears
3. Invoke it with a research-oriented prompt:

```text
$codex-autoresearch
Improve subject-heldout EEG classification quality without violating dataset integrity constraints.
```

Expected Convo behavior on a first run:

- Codex scans the repo for research signals
- If `research/*.yaml` is missing, it asks onboarding questions
- It proposes repo-grounded defaults for metric, split, verify, guards, and reports
- It asks you to choose `foreground` or `background`
- It waits for `go`

## First-run onboarding files

On a first run, Convo may create or refresh:

- `research/project.yaml`
- `research/datasets.yaml`
- `research/permissions.yaml`

New writes should use the richer canonical schema documented in [GUIDE.md](GUIDE.md), even if older flat YAML files still exist elsewhere.

## Returning runs

On a returning run, install is already complete. The main operational check is whether the canonical research memory still matches the current objective.

Convo should:

- read the existing memory before asking anything
- ask only for deltas
- preserve stable defaults

If the repo still uses a legacy schema, preview migration first:

```powershell
python PATH_TO_TARGET_REPO\.agents\skills\codex-autoresearch\scripts\research_migrate_schema.py --repo PATH_TO_TARGET_REPO --dry-run
```

Then apply it in place if the preview looks correct.

## Foreground and background prerequisites

### Foreground
- Runs inside the current Codex session
- Best for supervised runs and smoke tests
- No detached runtime control files are required

### Background
- Runs through the detached runtime controller
- Best for long or unattended loops
- Creates:
  - `autoresearch-launch.json`
  - `autoresearch-runtime.json`
  - `autoresearch-runtime.log`

Background mode only behaves as a true unattended run when the target repo is configured so Codex does not stop on every `git commit` or rollback operation.

## Trusted project notes on Windows

For Convo background runs, treat the target repo as trusted when appropriate so project-scoped `.codex/config.toml` can take effect and approvals do not interrupt normal runtime operations.

This matters especially for:

- `git commit`
- rollback actions
- detached runtime control

## BOM and LF precautions

On Windows, editors often rewrite files silently.

For this repo, prefer:

- UTF-8 **without BOM**
- LF line endings
- minimal CRLF churn in Markdown, YAML, TOML, rules, and helper scripts

This is especially important for:

- `*.md`
- `*.yaml` / `*.yml`
- `*.toml`
- `*.rules`
- helper scripts consumed across environments

## Multi-guard helper launches

When launching helper-driven runs, prefer repeated `--guard` flags:

```powershell
python PATH_TO_TARGET_REPO\.agents\skills\codex-autoresearch\scripts\autoresearch_runtime_ctl.py launch `
  --repo PATH_TO_TARGET_REPO `
  --goal "Improve subject-heldout EEG classification quality without violating dataset integrity constraints." `
  --metric AUROC `
  --direction higher `
  --verify "python eval_eeg.py --config configs/experiment.yaml --metric-only" `
  --guard "python guard_dataset.py" `
  --guard "python train_eeg.py --config configs/experiment.yaml"
```

Repeated `--guard` preserves structured guard metadata in:

- `autoresearch-state.json`
- `research-results.tsv`
- downstream reports

## Smoke-run snapshots

This repository includes smoke-run snapshots under `notes/smoke-runs/`.

Use them as reference material for:

- first-run research wording
- delta-only returning runs
- repeated-guard metadata
- report generation
- migration helper validation

## Updating

If installed by copy, replace the installed folder.

If installed by symlink or junction, update the source repo and restart Codex if the change is not picked up immediately.
