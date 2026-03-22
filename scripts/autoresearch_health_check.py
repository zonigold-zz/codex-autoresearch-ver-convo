#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from autoresearch_helpers import (
    AutoresearchError,
    command_is_executable,
    git_status_paths,
    has_git_repo,
    is_autoresearch_owned_artifact,
    lexical_abspath,
    parse_scope_patterns,
    path_is_in_scope,
    results_repo_root,
)
from autoresearch_resume_check import evaluate_resume_state


def run_health_check(
    *,
    repo: Path,
    results_path: Path,
    state_path_arg: str | None,
    verify_command: str,
    scope_text: str | None,
    min_free_mb: int,
) -> dict[str, Any]:
    warnings: list[str] = []
    blockers: list[str] = []

    free_mb = shutil.disk_usage(repo).free // (1024 * 1024)
    if free_mb < min_free_mb:
        blockers.append(f"disk free space below threshold: {free_mb}MB < {min_free_mb}MB")
    elif free_mb < max(min_free_mb * 2, 1000):
        warnings.append(f"disk free space is getting low: {free_mb}MB")

    resume = evaluate_resume_state(
        results_path=results_path,
        state_path_arg=state_path_arg,
        write_repaired_state=False,
    )
    state_path = Path(str(resume["state_path"]))

    if not bool(resume["has_results"]) and bool(resume["has_state"]):
        blockers.append("results log missing while state JSON exists; cannot track progress")
    elif str(resume["detail"]) == "state_without_reconstructable_tsv":
        blockers.append("results log is corrupt or unreconstructable; resume helper requires manual confirmation")
    elif str(resume["detail"]) == "unrecoverable_artifacts":
        blockers.extend(str(reason) for reason in resume["reasons"])
    elif str(resume["detail"]) == "state_tsv_diverged":
        warnings.append("state JSON diverges from the reconstructed TSV state; repair or mini-resume required")
    elif str(resume["detail"]) == "invalid_state_json":
        warnings.append("state JSON needs confirmation or repair, but TSV reconstruction is available")
    elif resume["decision"] == "tsv_fallback":
        warnings.append("results log exists without a trustworthy JSON state; resume would use TSV fallback")

    if has_git_repo(repo):
        dirty_lines = git_status_paths(repo)
        scope_patterns = parse_scope_patterns(scope_text)
        unexpected = []
        for path in dirty_lines:
            if not is_autoresearch_owned_artifact(path) and not path_is_in_scope(path, scope_patterns):
                unexpected.append(path)
        if unexpected:
            warnings.append("unexpected worktree changes: " + ", ".join(sorted(unexpected)))

    if not command_is_executable(verify_command):
        blockers.append(f"verify command is not executable: {verify_command}")

    decision = "ok"
    if blockers:
        decision = "block"
    elif warnings:
        decision = "warn"

    return {
        "decision": decision,
        "warnings": warnings,
        "blockers": blockers,
        "free_mb": free_mb,
        "results_path": str(results_path),
        "state_path": str(state_path),
        "has_results": bool(resume["has_results"]),
        "has_state": bool(resume["has_state"]),
        "main_rows": (
            int(resume["tsv_summary"]["main_rows"])
            if isinstance(resume.get("tsv_summary"), dict)
            else 0
        ),
        "resume_decision": resume["decision"],
        "resume_detail": resume["detail"],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the executable health checks for an autoresearch repo."
    )
    parser.add_argument("--repo")
    parser.add_argument("--results-path", default="research-results.tsv")
    parser.add_argument("--state-path")
    parser.add_argument("--verify-cmd", required=True)
    parser.add_argument("--scope")
    parser.add_argument("--min-free-mb", type=int, default=500)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    results_path = Path(args.results_path)
    repo = (
        lexical_abspath(Path(args.repo))
        if args.repo is not None
        else results_repo_root(
            lexical_abspath(results_path) if results_path.is_absolute() else results_path
        )
    )
    if not results_path.is_absolute():
        results_path = repo / results_path
    output = run_health_check(
        repo=repo,
        results_path=lexical_abspath(results_path),
        state_path_arg=args.state_path,
        verify_command=args.verify_cmd,
        scope_text=args.scope,
        min_free_mb=args.min_free_mb,
    )
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AutoresearchError as exc:
        raise SystemExit(f"error: {exc}")
