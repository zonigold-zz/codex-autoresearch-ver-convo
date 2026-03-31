from __future__ import annotations

import shutil
from pathlib import Path

import yaml

from .base import AutoresearchScriptsTestBase, REPO_ROOT


class ResearchMigrateSchemaTest(AutoresearchScriptsTestBase):
    def test_dry_run_reports_legacy_sample_changes_without_writing(self) -> None:
        repo = REPO_ROOT / "notes" / "smoke-runs" / "2026-03-30" / "legacy-lab"
        original_project = (repo / "project.yaml").read_text(encoding="utf-8")

        result = self.run_script(
            "research_migrate_schema.py",
            "--repo",
            str(repo),
            "--dry-run",
        )

        self.assertTrue(result["dry_run"])
        self.assertEqual(result["changed_files"], 3)
        self.assertEqual(result["files"]["project.yaml"]["status"], "would_change")
        self.assertEqual(result["files"]["datasets.yaml"]["status"], "would_change")
        self.assertEqual(result["files"]["permissions.yaml"]["status"], "would_change")
        self.assertEqual((repo / "project.yaml").read_text(encoding="utf-8"), original_project)
        self.assertFalse((repo / "project.yaml.bak").exists())

    def test_in_place_migration_writes_backups_and_canonical_shape(self) -> None:
        source_repo = REPO_ROOT / "notes" / "smoke-runs" / "2026-03-30" / "legacy-lab"
        repo = REPO_ROOT / "notes" / "smoke-runs" / "tmp-research-migrate-schema"
        if repo.exists():
            shutil.rmtree(repo)
        repo.mkdir(parents=True)
        for source_path in source_repo.iterdir():
            if source_path.is_file():
                shutil.copy2(source_path, repo / source_path.name)
        try:
            result = self.run_script(
                "research_migrate_schema.py",
                "--repo",
                str(repo),
            )

            self.assertFalse(result["dry_run"])
            self.assertEqual(result["changed_files"], 3)
            for name in ("project.yaml", "datasets.yaml", "permissions.yaml"):
                self.assertEqual(result["files"][name]["status"], "changed")
                self.assertTrue((repo / f"{name}.bak").exists())

            project_data = yaml.safe_load((repo / "project.yaml").read_text(encoding="utf-8"))
            self.assertEqual(
                project_data["goal"],
                "Improve subject-heldout EEG classification while keeping the workflow conversational and researcher-friendly.",
            )
            self.assertEqual(project_data["task_family"], "classification")
            self.assertEqual(project_data["objective"]["primary_metric"], "AUROC")
            self.assertEqual(project_data["verify"]["status"], "migrated_from_legacy_schema")
            self.assertEqual(
                project_data["guards"],
                [
                    "python train_eeg.py --config configs/experiment.yaml",
                    "python guard_dataset.py",
                ],
            )

            datasets_data = yaml.safe_load((repo / "datasets.yaml").read_text(encoding="utf-8"))
            self.assertEqual(datasets_data["datasets"][0]["role"], "primary")
            self.assertEqual(datasets_data["datasets"][0]["label_unit"], "subject")
            self.assertEqual(datasets_data["datasets"][0]["raw_data_mutability"], "immutable")
            self.assertEqual(
                datasets_data["datasets"][0]["schema"],
                {"legacy_fields": {"label_field": "label"}},
            )

            permissions_data = yaml.safe_load((repo / "permissions.yaml").read_text(encoding="utf-8"))
            self.assertIn("permissions", permissions_data)
            self.assertFalse(permissions_data["permissions"]["raw_data"]["mutation_allowed"])
            self.assertIn("Legacy profile: research-safe", permissions_data["guardrails"])
            self.assertTrue(permissions_data["launch_policy"]["require_user_go"])
        finally:
            shutil.rmtree(repo, ignore_errors=True)

    def test_rich_sample_is_left_unchanged(self) -> None:
        repo = REPO_ROOT / "notes" / "smoke-runs" / "2026-03-30" / "fresh-lab"
        before = {
            name: (repo / name).read_text(encoding="utf-8")
            for name in ("project.yaml", "datasets.yaml", "permissions.yaml")
        }

        result = self.run_script(
            "research_migrate_schema.py",
            "--repo",
            str(repo),
            "--dry-run",
        )

        self.assertEqual(result["changed_files"], 0)
        self.assertEqual(result["unchanged_files"], 3)
        for name in before:
            self.assertEqual(result["files"][name]["status"], "unchanged")
            self.assertEqual((repo / name).read_text(encoding="utf-8"), before[name])
