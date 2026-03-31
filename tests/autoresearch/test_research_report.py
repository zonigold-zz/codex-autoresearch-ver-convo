from __future__ import annotations

from pathlib import Path

from .base import AutoresearchScriptsTestBase, REPO_ROOT


class ResearchReportTest(AutoresearchScriptsTestBase):
    def test_report_uses_metadata_preamble_and_nested_state_fields(self) -> None:
        repo = REPO_ROOT / "notes" / "smoke-runs" / "2026-03-31-regression-rerun" / "regression-lab"
        output = "reports/generated_test_report.md"

        result = self.run_script(
            "research_report.py",
            "--repo",
            str(repo),
            "--output",
            output,
        )

        self.assertEqual(result["iterations"], 1)
        report = (repo / output).read_text(encoding="utf-8")

        for heading in (
            "## Objective",
            "## Metric and verification",
            "## Dataset and split assumptions",
            "## Guards and safety constraints",
            "## Best retained result",
            "## Key changes tried",
            "## Open blockers",
            "## Recommended next actions",
        ):
            self.assertIn(heading, report)

        self.assertIn(
            "- Improve subject-heldout EEG classification quality without violating dataset integrity constraints.",
            report,
        )
        self.assertIn("- Metric: `AUROC` (higher is better)", report)
        self.assertIn(
            "- Verification command: `python eval_eeg.py --config configs/experiment.yaml --metric-only`",
            report,
        )
        self.assertIn(
            "- Dataset-related paths in declared scope: `data/sample-eeg/labels.csv`",
            report,
        )
        self.assertIn("- Split assumption mentioned in artifacts: `subject-heldout`", report)
        self.assertIn("- Guard 1: `python guard_dataset.py`", report)
        self.assertIn(
            "- Guard 2: `python train_eeg.py --config configs/experiment.yaml`",
            report,
        )
        self.assertIn("- Best retained metric: `1`", report)
        self.assertIn("- Retained commit: `7c6fa7f`", report)
        self.assertIn("- Moved subject score assignments into configs/experiment.yaml.", report)
        self.assertIn(
            "- Made eval_eeg.py consume config-defined scores for subject-heldout AUROC.",
            report,
        )
        self.assertIn(
            "Current evaluation path appears to depend on config-provided subject scores rather than model-produced predictions.",
            report,
        )
        self.assertIn(
            "replace the score table with model-produced predictions while preserving the current verify and guard commands.",
            report,
        )

        Path(repo / output).unlink(missing_ok=True)
