from __future__ import annotations

import json
import tempfile
from pathlib import Path

from .base import AutoresearchScriptsTestBase


class AutoresearchForegroundModeTest(AutoresearchScriptsTestBase):
    maxDiff = None

    def test_foreground_init_creates_only_results_and_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            results_path = repo / "research-results.tsv"
            state_path = repo / "autoresearch-state.json"

            result = self.run_script(
                "autoresearch_init_run.py",
                "--results-path",
                str(results_path),
                "--state-path",
                str(state_path),
                "--mode",
                "loop",
                "--goal",
                "Reduce failures",
                "--scope",
                "src/**/*.py",
                "--metric-name",
                "failure count",
                "--direction",
                "lower",
                "--verify",
                "pytest -q",
                "--baseline-metric",
                "10",
                "--baseline-commit",
                "a1b2c3d",
                "--baseline-description",
                "baseline failures",
            )

            self.assertEqual(result["session_mode"], "foreground")
            self.assertTrue(results_path.exists())
            self.assertTrue(state_path.exists())
            self.assertFalse((repo / "autoresearch-launch.json").exists())
            self.assertFalse((repo / "autoresearch-runtime.json").exists())
            self.assertFalse((repo / "autoresearch-runtime.log").exists())

            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(state["session_mode"], "foreground")
            self.assertEqual(state["config"]["session_mode"], "foreground")
            self.assertNotIn("execution_policy", state["config"])

    def test_foreground_multi_repo_state_keeps_repo_targets_without_runtime_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            primary = root / "primary"
            companion = root / "companion"
            primary.mkdir()
            companion.mkdir()

            self.run_script(
                "autoresearch_init_run.py",
                "--results-path",
                str(primary / "research-results.tsv"),
                "--state-path",
                str(primary / "autoresearch-state.json"),
                "--mode",
                "loop",
                "--goal",
                "Coordinate repos",
                "--scope",
                "src/",
                "--companion-repo-scope",
                f"{companion}=pkg/",
                "--metric-name",
                "failure count",
                "--direction",
                "lower",
                "--verify",
                "python3 -c pass",
                "--baseline-metric",
                "10",
                "--baseline-commit",
                "base111",
                "--repo-commit",
                f"{companion}=comp111",
                "--baseline-description",
                "baseline failures",
            )

            state = json.loads((primary / "autoresearch-state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["session_mode"], "foreground")
            self.assertEqual(
                state["config"]["repos"],
                [
                    {"path": str(primary.resolve()), "scope": "src/", "role": "primary"},
                    {"path": str(companion.resolve()), "scope": "pkg/", "role": "companion"},
                ],
            )
            self.assertFalse((primary / "autoresearch-launch.json").exists())
            self.assertFalse((primary / "autoresearch-runtime.json").exists())
