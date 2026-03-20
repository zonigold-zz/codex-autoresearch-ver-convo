from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "check_skill_invariants.py"


class CheckSkillInvariantsTest(unittest.TestCase):
    def run_invariant_check(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            capture_output=True,
            text=True,
        )

    def test_exec_expect_improvement_supports_higher_direction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "research-results.tsv").write_text(
                "\n".join(
                    [
                        "# metric_direction: higher",
                        "iteration\tcommit\tmetric\tdelta\tguard\tstatus\tdescription",
                        "0\tbase123\t10\t0\t-\tbaseline\tbaseline score",
                        "1\tkeep123\t12\t+2\tpass\tkeep\timproved score",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (repo / "autoresearch-lessons.md").write_text("# lessons\n", encoding="utf-8")

            completed = self.run_invariant_check(
                "exec",
                "--repo",
                str(repo),
                "--expect-improvement",
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("exec invariants: OK", completed.stdout)

    def test_exec_invariants_reject_keep_rows_without_commit_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "research-results.tsv").write_text(
                "\n".join(
                    [
                        "# metric_direction: lower",
                        "iteration\tcommit\tmetric\tdelta\tguard\tstatus\tdescription",
                        "0\tbase123\t10\t0\t-\tbaseline\tbaseline score",
                        "1\t-\t8\t-2\tpass\tkeep\tinvalid keep row",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (repo / "autoresearch-lessons.md").write_text("# lessons\n", encoding="utf-8")

            completed = self.run_invariant_check("exec", "--repo", str(repo))

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("missing a commit hash", completed.stderr)

    def test_exec_invariants_reject_event_logs_without_bundled_helper_usage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            event_log = repo / "events.jsonl"
            (repo / "research-results.tsv").write_text(
                "\n".join(
                    [
                        "# metric_direction: lower",
                        "iteration\tcommit\tmetric\tdelta\tguard\tstatus\tdescription",
                        "0\tbase123\t10\t0\t-\tbaseline\tbaseline score",
                        "1\tkeep123\t8\t-2\tpass\tkeep\timproved score",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (repo / "autoresearch-lessons.md").write_text("# lessons\n", encoding="utf-8")
            event_log.write_text(
                'command: python3 scripts/autoresearch_init_run.py\n',
                encoding="utf-8",
            )

            completed = self.run_invariant_check(
                "exec",
                "--repo",
                str(repo),
                "--event-log",
                str(event_log),
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("bundled helper scripts", completed.stderr)

    def test_exec_invariants_accept_bundled_helper_usage_in_event_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            event_log = repo / "events.jsonl"
            (repo / "research-results.tsv").write_text(
                "\n".join(
                    [
                        "# metric_direction: lower",
                        "iteration\tcommit\tmetric\tdelta\tguard\tstatus\tdescription",
                        "0\tbase123\t10\t0\t-\tbaseline\tbaseline score",
                        "1\tkeep123\t8\t-2\tpass\tkeep\timproved score",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (repo / "autoresearch-lessons.md").write_text("# lessons\n", encoding="utf-8")
            event_log.write_text(
                "\n".join(
                    [
                        'command: python3 .agents/skills/codex-autoresearch/scripts/autoresearch_init_run.py --mode exec',
                        'command: python3 .agents/skills/codex-autoresearch/scripts/autoresearch_record_iteration.py --status keep',
                        'command: python3 .agents/skills/codex-autoresearch/scripts/autoresearch_exec_state.py --cleanup',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            completed = self.run_invariant_check(
                "exec",
                "--repo",
                str(repo),
                "--event-log",
                str(event_log),
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("exec invariants: OK", completed.stdout)

    def test_exec_invariants_accept_admin_scope_skill_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            event_log = repo / "events.jsonl"
            (repo / "research-results.tsv").write_text(
                "\n".join(
                    [
                        "# metric_direction: lower",
                        "iteration\tcommit\tmetric\tdelta\tguard\tstatus\tdescription",
                        "0\tbase123\t10\t0\t-\tbaseline\tbaseline score",
                        "1\tkeep123\t8\t-2\tpass\tkeep\timproved score",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (repo / "autoresearch-lessons.md").write_text("# lessons\n", encoding="utf-8")
            event_log.write_text(
                "\n".join(
                    [
                        "command: python3 /etc/codex/skills/codex-autoresearch/scripts/autoresearch_init_run.py --mode exec",
                        "command: python3 /etc/codex/skills/codex-autoresearch/scripts/autoresearch_record_iteration.py --status keep",
                        "command: python3 /etc/codex/skills/codex-autoresearch/scripts/autoresearch_exec_state.py --cleanup",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            completed = self.run_invariant_check(
                "exec",
                "--repo",
                str(repo),
                "--event-log",
                str(event_log),
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("exec invariants: OK", completed.stdout)


if __name__ == "__main__":
    unittest.main()
