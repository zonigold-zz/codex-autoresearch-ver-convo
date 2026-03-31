# Installation

This page covers installation and local-development notes for the Convo variant.

---

## Recommended Layout

For this repo, prefer a repo-local install so the skill and the research-oriented docs travel with the project:

```text
<target-repo>\
  .agents\
    skills\
      codex-autoresearch  -> this repo
```

That keeps the Convo variant active only where you want its research-memory behavior.

## Install Options

### Skill installer

```text
$skill-installer install https://github.com/leo-lilinxiao/codex-autoresearch
```

Restart Codex after installation changes.

### Copy install

```powershell
git clone https://github.com/leo-lilinxiao/codex-autoresearch.git
Copy-Item -Recurse codex-autoresearch <target-repo>\.agents\skills\codex-autoresearch
```

### Repo-local symlink or junction

This is the preferred Windows development setup for the Convo variant because doc and prompt edits become live immediately.

PowerShell symbolic link:

```powershell
New-Item -ItemType SymbolicLink `
  -Path <target-repo>\.agents\skills\codex-autoresearch `
  -Target F:\repos\codex-autoresearch-ver-convo
```

If developer-mode symlinks are unavailable, use a junction:

```powershell
cmd /c mklink /J <target-repo>\.agents\skills\codex-autoresearch F:\repos\codex-autoresearch-ver-convo
```

## Verify the Install

Open Codex in the target repo and verify:

1. Type `$` and confirm `codex-autoresearch` appears.
2. Invoke it with a research-oriented prompt:

```text
$codex-autoresearch
Improve subject-heldout EEG classification quality without violating dataset integrity constraints.
```

Expected first-run behavior in Convo:

- Codex reads the repo and looks for existing research memory.
- If memory is missing, it asks onboarding questions.
- It proposes defaults for metric, split, guards, and reports.
- It asks you to choose `foreground` or `background`.
- It waits for `go`.

## First-Run Onboarding Files

On a first run, Convo may create or refresh these canonical research memory files:

- `project.yaml`
- `datasets.yaml`
- `permissions.yaml`

New writes should use the richer schema documented in [GUIDE.md](GUIDE.md), even when the repo still contains older flat YAMLs elsewhere.

## Returning Runs

On a returning run, the install is already complete; the main operational check is whether the canonical research memory still matches the current objective.

Convo should:

- read the existing memory before asking anything
- ask only for deltas
- preserve stable defaults

If the repo materially changed and still uses a legacy memory shape, run:

```powershell
python scripts\research_migrate_schema.py --repo <target-repo> --dry-run
```

## Foreground and Background Prerequisites

### Foreground

- Works in the current Codex session.
- Best for supervised runs or smoke tests.
- No runtime control files are required.

### Background

- Requires the repo to be effectively trusted for unattended `git commit` and rollback operations.
- Best for overnight or detached runs.
- Creates `autoresearch-launch.json`, `autoresearch-runtime.json`, and `autoresearch-runtime.log`.

If approvals or sandboxing interrupt normal git operations, background mode will not behave like a true unattended launch.

## Trusted Project Notes on Windows

For Convo background runs, treat the target repo as trusted when appropriate so Codex does not stop on each commit/revert decision. This is especially important for long-running research loops where the point of background mode is to continue after `go` without operator interaction.

## BOM and LF Precautions

Windows editors often change encoding or line endings silently. For this repo:

- prefer UTF-8 without BOM
- prefer LF line endings
- avoid introducing CRLF churn in Markdown and YAML
- check diffs if an editor rewrites untouched files

This matters because Markdown, YAML, and prompt metadata are consumed on both Windows and Unix-like environments.

## Multi-Guard Helper Launches

When launching through helper scripts, prefer repeated `--guard` flags:

```powershell
python .agents\skills\codex-autoresearch\scripts\autoresearch_runtime_ctl.py launch `
  --repo F:\lab\convo-skill-regression-lab `
  --goal "Improve subject-heldout EEG classification quality without violating dataset integrity constraints." `
  --metric AUROC `
  --direction higher `
  --verify "python eval_eeg.py --config configs/experiment.yaml --metric-only" `
  --guard "python guard_dataset.py" `
  --guard "python train_eeg.py --config configs/experiment.yaml"
```

Repeated `--guard` keeps guard metadata structured in `autoresearch-state.json`, `research-results.tsv`, and reporting output.

## EEG Smoke-Run Fixture

This repo's current regression example lives at:

- [research-results.tsv](F:\repos\codex-autoresearch-ver-convo\notes\smoke-runs\2026-03-31-regression-rerun\regression-lab\research-results.tsv)
- [autoresearch-state.json](F:\repos\codex-autoresearch-ver-convo\notes\smoke-runs\2026-03-31-regression-rerun\regression-lab\autoresearch-state.json)

Use it as a post-install smoke reference for:

- first-run research wording
- repeated-guard metadata
- report generation
- foreground session-mode recording

## Updating

If installed by copy, replace the installed folder.

If installed by symlink or junction, update the source repo and restart Codex if the change is not picked up immediately.
