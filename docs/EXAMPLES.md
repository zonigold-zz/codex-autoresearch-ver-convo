# Examples

These examples are specific to the Convo variant. They focus on the conversational onboarding flow, returning-run delta-only behavior, and helper launches with repeated guards.

---

## Table of Contents

- [First-Run Research Onboarding](#first-run-research-onboarding)
- [Returning-Run Delta-Only Flow](#returning-run-delta-only-flow)
- [Foreground and Background `go`](#foreground-and-background-go)
- [EEG Regression Smoke Run](#eeg-regression-smoke-run)
- [Repeated `--guard` Launches](#repeated---guard-launches)
- [Memory Migration and Reporting](#memory-migration-and-reporting)

---

## First-Run Research Onboarding

User prompt:

```text
$codex-autoresearch
Improve subject-heldout EEG classification quality without violating dataset integrity constraints.
```

Expected Convo setup behavior on a repo with no canonical research memory:

```text
Codex: I found a research-style repo and no canonical memory files yet.

       Confirmed so far:
       - Goal: improve subject-heldout EEG classification quality
       - Likely task family: classification

       Need to confirm:
       - Metric and direction: is AUROC / higher correct?
       - Split policy: keep subject-heldout?
       - Raw data policy: immutable?
       - Guards: should dataset integrity and training both stay green?
       - Run mode: foreground or background?

       I will write project.yaml, datasets.yaml, and permissions.yaml after you confirm.
```

Typical user reply:

```text
AUROC, higher. Keep subject-heldout. Raw data stays immutable.
Use dataset guard plus training smoke. Foreground. Go.
```

Expected outcome before iteration 1:

- `project.yaml` exists with the richer schema
- `datasets.yaml` exists with split and mutability assumptions
- `permissions.yaml` exists with launch policy and guardrails
- the active run starts only after `go`

## Returning-Run Delta-Only Flow

User prompt:

```text
$codex-autoresearch
Continue the EEG work, but add a faster smoke guard and keep everything else the same.
```

Expected Convo behavior on a repo that already has canonical memory:

```text
Codex: I read the existing research memory.

       Stable defaults retained:
       - Goal family: EEG classification
       - Split: subject-heldout
       - Primary metric: AUROC / higher

       Need to confirm the delta only:
       - Add the new smoke guard in addition to the existing guards?
       - Run mode this time: foreground or background?
```

The important property is what Convo does not do: it does not ask again for the original task family, split, dataset role, or report targets unless the user changed them.

## Foreground and Background `go`

Foreground example:

```text
You:   $codex-autoresearch
       Reduce failing tests in this repo.

Codex: [setup questions]

You:   Foreground. Go.
```

Expected behavior:

- the loop stays in the current Codex session
- no `autoresearch-launch.json`
- no `autoresearch-runtime.json`
- no `autoresearch-runtime.log`

Background example:

```text
You:   $codex-autoresearch
       Improve the EEG metric overnight with the existing guards.

Codex: [setup questions]

You:   Background. Go.
```

Expected behavior:

- the loop is handed to the detached runtime controller
- `autoresearch-launch.json` is written
- `autoresearch-runtime.json` is written
- `autoresearch-runtime.log` is written

In both modes, `go` is the launch boundary. Before `go`, setup is interactive. After `go`, the run is autonomous.

## EEG Regression Smoke Run

The current regression fixture is:

- [research-results.tsv](F:\repos\codex-autoresearch-ver-convo\notes\smoke-runs\2026-03-31-regression-rerun\regression-lab\research-results.tsv)
- [autoresearch-state.json](F:\repos\codex-autoresearch-ver-convo\notes\smoke-runs\2026-03-31-regression-rerun\regression-lab\autoresearch-state.json)

Observed fixture values:

- Goal: `Improve subject-heldout EEG classification quality without violating dataset integrity constraints.`
- Verify: `python eval_eeg.py --config configs/experiment.yaml --metric-only`
- Guard 1: `python guard_dataset.py`
- Guard 2: `python train_eeg.py --config configs/experiment.yaml`
- Baseline AUROC: `0.75`
- Best retained AUROC: `1.0`
- Session mode: `foreground`

Minimal smoke-run narrative:

```text
$codex-autoresearch
Improve subject-heldout EEG classification quality without violating dataset integrity constraints.

Foreground. Go.
```

The fixture's retained keep was:

```text
Moved subject score assignments into configs/experiment.yaml and made eval_eeg.py consume config-defined scores for subject-heldout AUROC.
```

That makes it a good regression fixture for:

- research-memory-aware setup
- foreground launch semantics
- repeated guard recording
- report generation from state + TSV

## Repeated `--guard` Launches

Preferred helper launch:

```powershell
python .agents\skills\codex-autoresearch\scripts\autoresearch_runtime_ctl.py launch `
  --repo PATH_TO_REGRESSION_FIXTURE `
  --goal "Improve subject-heldout EEG classification quality without violating dataset integrity constraints." `
  --metric AUROC `
  --direction higher `
  --verify "python eval_eeg.py --config configs/experiment.yaml --metric-only" `
  --guard "python guard_dataset.py" `
  --guard "python train_eeg.py --config configs/experiment.yaml"
```

Avoid this unless you intentionally want one composite shell command:

```powershell
--guard "python guard_dataset.py && python train_eeg.py --config configs/experiment.yaml"
```

Why repeated `--guard` is better here:

- each guard survives as a structured list
- reports can enumerate guards cleanly
- TSV metadata can preserve the original guard sequence
- shell quoting stays simpler across Windows and Unix environments

## Memory Migration and Reporting

Legacy memory migration dry run:

```powershell
python scripts\research_migrate_schema.py `
  --repo F:\repos\codex-autoresearch-ver-convo\notes\smoke-runs\2026-03-30\legacy-lab `
  --dry-run
```

Generate a researcher-readable report from the current regression rerun:

```powershell
python scripts\research_report.py `
  --repo F:\repos\codex-autoresearch-ver-convo\notes\smoke-runs\2026-03-31-regression-rerun\regression-lab
```

Use these examples when verifying:

- first-run onboarding writes the richer schema
- returning runs ask only for deltas
- repeated guard metadata survives into reports
- the Convo docs match the actual regression fixture
