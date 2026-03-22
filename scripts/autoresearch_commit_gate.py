#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from autoresearch_helpers import (
    AutoresearchError,
    git_status_entries,
    is_autoresearch_owned_artifact,
    parse_scope_patterns,
    path_is_in_scope,
)


def evaluate_commit_gate(
    *,
    repo: Path,
    phase: str,
    rollback_policy: str | None,
    destructive_approved: bool,
    scope_text: str | None = None,
) -> dict[str, Any]:
    status_entries = git_status_entries(repo)
    unexpected_worktree = []
    staged_artifacts = []
    scope_patterns = parse_scope_patterns(scope_text)
    phase_labels = {
        "prelaunch": "before launch",
        "precommit": "before commit",
        "prebatch": "before parallel batch",
    }

    for entry in status_entries:
        for raw_path in entry.touched_paths:
            if not is_autoresearch_owned_artifact(raw_path) and not path_is_in_scope(raw_path, scope_patterns):
                unexpected_worktree.append(raw_path)
            if entry.has_staged_change and is_autoresearch_owned_artifact(raw_path):
                staged_artifacts.append(raw_path)

    blockers: list[str] = []
    warnings: list[str] = []
    if phase in phase_labels and unexpected_worktree:
        label = phase_labels[phase]
        blockers.append(
            f"unexpected worktree changes {label}: " + ", ".join(sorted(unexpected_worktree))
        )
    elif unexpected_worktree:
        warnings.append("unexpected worktree changes: " + ", ".join(sorted(unexpected_worktree)))

    if staged_artifacts:
        blockers.append("autoresearch-owned artifacts are staged: " + ", ".join(sorted(staged_artifacts)))

    if rollback_policy == "destructive" and not destructive_approved:
        blockers.append("destructive rollback requested without prior approval")

    decision = "allow"
    if blockers:
        decision = "block"
    elif warnings:
        decision = "warn"
    return {
        "decision": decision,
        "phase": phase,
        "rollback_policy": rollback_policy or "",
        "destructive_approved": destructive_approved,
        "scope_patterns": scope_patterns,
        "unexpected_worktree": sorted(unexpected_worktree),
        "staged_artifacts": sorted(staged_artifacts),
        "warnings": warnings,
        "blockers": blockers,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate git cleanliness and artifact staging rules for autoresearch."
    )
    parser.add_argument("--repo", default=".")
    parser.add_argument(
        "--phase",
        choices=["prelaunch", "precommit", "prebatch", "rollback"],
        default="precommit",
    )
    parser.add_argument("--rollback-policy")
    parser.add_argument("--destructive-approved", action="store_true")
    parser.add_argument("--scope")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    output = evaluate_commit_gate(
        repo=Path(args.repo).resolve(),
        phase=args.phase,
        rollback_policy=args.rollback_policy,
        destructive_approved=args.destructive_approved,
        scope_text=args.scope,
    )
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AutoresearchError as exc:
        raise SystemExit(f"error: {exc}")
