#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml


TARGET_FILES = ("project.yaml", "datasets.yaml", "permissions.yaml")
PROJECT_CANONICAL_KEYS = {
    "goal",
    "task_family",
    "primary_repo",
    "scope",
    "objective",
    "split_policy",
    "verify",
    "guards",
    "artifacts",
    "notes",
}
DATASET_CANONICAL_KEYS = {
    "name",
    "path",
    "role",
    "modality",
    "label_source",
    "label_unit",
    "target_type",
    "split_policy",
    "raw_data_mutability",
    "known_files",
    "schema",
    "assumptions",
}
PERMISSIONS_CANONICAL_KEYS = {"permissions", "guardrails", "launch_policy"}


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8-sig"))


def dump_yaml(data: Any) -> str:
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=False)


def infer_file_locations(repo_root: Path) -> dict[str, Path]:
    research_dir = repo_root / "research"
    if research_dir.is_dir():
        return {name: research_dir / name for name in TARGET_FILES}
    return {name: repo_root / name for name in TARGET_FILES}


def coerce_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def normalize_path_list(values: list[Any]) -> list[str]:
    return [str(item) for item in values if item not in (None, "")]


def infer_split_policy(project_data: dict[str, Any], datasets_data: dict[str, Any]) -> str:
    value = project_data.get("split_policy")
    if isinstance(value, str) and value.strip():
        return value
    datasets = datasets_data.get("datasets")
    if isinstance(datasets, list):
        policies = []
        for item in datasets:
            if isinstance(item, dict):
                policy = item.get("split_policy")
                if isinstance(policy, str) and policy.strip():
                    policies.append(policy)
        unique = list(dict.fromkeys(policies))
        if len(unique) == 1:
            return unique[0]
    return ""


def migrate_project(project_data: Any, datasets_data: Any, repo_root: Path) -> tuple[Any, dict[str, Any] | None]:
    if not isinstance(project_data, dict):
        return project_data, None
    if PROJECT_CANONICAL_KEYS.issubset(project_data.keys()):
        return project_data, None

    old_keys = {
        "project_name",
        "research_goal",
        "paradigm",
        "domain",
        "primary_metric",
        "verify_command",
        "guard_commands",
        "default_run_mode",
        "max_iterations",
        "run_profile",
        "report_outputs",
    }
    if not (set(project_data.keys()) & old_keys):
        return project_data, None

    primary_metric = project_data.get("primary_metric")
    metric_name = ""
    direction = ""
    if isinstance(primary_metric, dict):
        metric_name = str(primary_metric.get("name", "") or "")
        direction = str(primary_metric.get("direction", "") or "")

    notes: list[str] = []
    if project_data.get("project_name"):
        notes.append(f"Legacy project_name: {project_data['project_name']}")
    if project_data.get("domain"):
        notes.append(f"Legacy domain: {project_data['domain']}")
    if project_data.get("run_profile"):
        notes.append(f"Legacy run_profile: {project_data['run_profile']}")
    if project_data.get("max_iterations") not in (None, ""):
        notes.append(f"Legacy max_iterations: {project_data['max_iterations']}")

    migrated = {
        "goal": str(project_data.get("research_goal", "") or ""),
        "task_family": str(project_data.get("paradigm", "") or ""),
        "primary_repo": str(repo_root),
        "scope": normalize_path_list(
            [
                "research/project.yaml",
                "research/datasets.yaml",
                "research/permissions.yaml",
            ]
        ),
        "objective": {
            "target": str(project_data.get("research_goal", "") or ""),
            "primary_metric": metric_name,
            "direction": direction,
        },
        "split_policy": infer_split_policy(project_data, datasets_data if isinstance(datasets_data, dict) else {}),
        "verify": {
            "command": str(project_data.get("verify_command", "") or ""),
            "status": "migrated_from_legacy_schema",
        },
        "guards": normalize_path_list(coerce_list(project_data.get("guard_commands"))),
        "artifacts": normalize_path_list(coerce_list(project_data.get("report_outputs"))),
        "notes": notes,
    }
    return migrated, {"migrated_from": "legacy"}


def infer_target_type(legacy_dataset: dict[str, Any], task_family: str) -> str:
    if task_family == "classification":
        metric_name = str(legacy_dataset.get("label_field", "") or "").lower()
        return "classification" if metric_name else "classification"
    if task_family == "regression":
        return "regression"
    if task_family:
        return task_family
    return ""


def migrate_datasets(datasets_data: Any, project_data: Any) -> tuple[Any, dict[str, Any] | None]:
    if not isinstance(datasets_data, dict):
        return datasets_data, None
    datasets = datasets_data.get("datasets")
    if not isinstance(datasets, list):
        return datasets_data, None
    if all(isinstance(item, dict) and DATASET_CANONICAL_KEYS.issubset(item.keys()) for item in datasets):
        return datasets_data, None

    legacy_fields = {
        "sample_unit",
        "label_field",
        "raw_data_mutable",
        "contains_sensitive_data",
    }
    if not any(isinstance(item, dict) and (set(item.keys()) & legacy_fields) for item in datasets):
        return datasets_data, None

    task_family = ""
    if isinstance(project_data, dict):
        task_family = str(
            project_data.get("task_family")
            or project_data.get("paradigm")
            or ""
        )

    migrated_items = []
    for item in datasets:
        if not isinstance(item, dict):
            migrated_items.append(item)
            continue
        split_policy = str(item.get("split_policy", "") or "")
        path_value = str(item.get("path", "") or "")
        name_value = str(item.get("name", "") or "")
        label_field = str(item.get("label_field", "") or "")
        label_source = path_value
        if label_field:
            label_source = f"{path_value}#{label_field}" if path_value else label_field

        assumptions = []
        if "contains_sensitive_data" in item:
            assumptions.append(
                f"Legacy contains_sensitive_data: {bool(item.get('contains_sensitive_data'))}"
            )

        migrated_items.append(
            {
                "name": name_value,
                "path": path_value,
                "role": "primary",
                "modality": str(item.get("modality", "") or ""),
                "label_source": label_source,
                "label_unit": str(item.get("sample_unit", "") or ""),
                "target_type": infer_target_type(item, task_family),
                "split_policy": split_policy,
                "raw_data_mutability": "mutable"
                if bool(item.get("raw_data_mutable"))
                else "immutable",
                "known_files": normalize_path_list([path_value] if path_value else []),
                "schema": {"legacy_fields": {"label_field": label_field}} if label_field else {},
                "assumptions": assumptions,
            }
        )
    return {"datasets": migrated_items}, {"migrated_from": "legacy", "datasets": len(migrated_items)}


def migrate_permissions(permissions_data: Any) -> tuple[Any, dict[str, Any] | None]:
    if not isinstance(permissions_data, dict):
        return permissions_data, None
    if PERMISSIONS_CANONICAL_KEYS.issubset(permissions_data.keys()):
        return permissions_data, None

    old_keys = {
        "profile",
        "allow_network",
        "allow_git_commit",
        "allow_git_push",
        "allow_raw_data_write",
        "allow_report_write",
        "allow_branch_creation",
    }
    if not (set(permissions_data.keys()) & old_keys):
        return permissions_data, None

    allow_raw_data_write = permissions_data.get("allow_raw_data_write")
    report_paths: list[str] = []
    if permissions_data.get("allow_report_write"):
        report_paths = ["reports/latest_run.md", "reports/methods_draft.md"]

    guardrails = []
    if permissions_data.get("profile"):
        guardrails.append(f"Legacy profile: {permissions_data['profile']}")
    guardrails.append(
        "Legacy allow_network: "
        + ("enabled" if bool(permissions_data.get("allow_network")) else "disabled")
    )
    guardrails.append(f"Legacy allow_git_push: {permissions_data.get('allow_git_push', '')}")
    guardrails.append(
        f"Legacy allow_git_commit: {permissions_data.get('allow_git_commit', '')}"
    )
    if permissions_data.get("allow_branch_creation") is not None:
        guardrails.append(
            "Legacy allow_branch_creation: "
            + ("enabled" if bool(permissions_data.get("allow_branch_creation")) else "disabled")
        )

    migrated = {
        "permissions": {
            "raw_data": {
                "path": "data",
                "policy": "read_write"
                if allow_raw_data_write not in ("forbidden", False, None)
                else "read_only",
                "mutation_allowed": bool(allow_raw_data_write not in ("forbidden", False, None)),
            },
            "code": {
                "allowed_paths": [
                    "research/project.yaml",
                    "research/datasets.yaml",
                    "research/permissions.yaml",
                ]
            },
            "reports": {"allowed_paths": report_paths},
        },
        "guardrails": guardrails,
        "launch_policy": {
            "require_user_go": permissions_data.get("allow_git_commit") == "prompt",
            "default_mode": "undecided",
        },
    }
    return migrated, {"migrated_from": "legacy"}


def next_backup_path(path: Path) -> Path:
    candidate = path.with_name(path.name + ".bak")
    if not candidate.exists():
        return candidate
    index = 2
    while True:
        candidate = path.with_name(f"{path.name}.bak.{index}")
        if not candidate.exists():
            return candidate
        index += 1


def migrate_repo(repo_root: Path, dry_run: bool) -> dict[str, Any]:
    file_locations = infer_file_locations(repo_root)
    loaded: dict[str, Any] = {}
    summary_files: dict[str, dict[str, Any]] = {}

    for name, path in file_locations.items():
        if path.exists():
            loaded[name] = load_yaml(path)
        else:
            loaded[name] = None
            summary_files[name] = {"status": "missing", "path": str(path)}

    migrations = {
        "project.yaml": migrate_project(loaded.get("project.yaml"), loaded.get("datasets.yaml"), repo_root),
        "datasets.yaml": migrate_datasets(loaded.get("datasets.yaml"), loaded.get("project.yaml")),
        "permissions.yaml": migrate_permissions(loaded.get("permissions.yaml")),
    }

    changed_count = 0
    unchanged_count = 0

    for name in TARGET_FILES:
        path = file_locations[name]
        original_data = loaded.get(name)
        migrated_data, details = migrations[name]
        if not path.exists():
            continue
        if details is None or migrated_data == original_data:
            summary_files.setdefault(name, {"path": str(path)})
            summary_files[name]["status"] = "unchanged"
            unchanged_count += 1
            continue

        original_text = path.read_text(encoding="utf-8-sig")
        new_text = dump_yaml(migrated_data)
        backup_path = None
        if not dry_run:
            backup_path = next_backup_path(path)
            backup_path.write_text(original_text, encoding="utf-8", newline="\n")
            path.write_text(new_text, encoding="utf-8", newline="\n")

        summary_files[name] = {
            "status": "would_change" if dry_run else "changed",
            "path": str(path),
            "backup_path": str(backup_path) if backup_path else None,
            "details": details,
        }
        changed_count += 1

    return {
        "repo": str(repo_root),
        "dry_run": dry_run,
        "changed_files": changed_count,
        "unchanged_files": unchanged_count,
        "files": summary_files,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Migrate legacy research memory YAML files to the richer canonical schema."
    )
    parser.add_argument("--repo", required=True, help="Target repository root")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report changes without modifying files",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo).resolve()
    result = migrate_repo(repo_root, dry_run=args.dry_run)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
