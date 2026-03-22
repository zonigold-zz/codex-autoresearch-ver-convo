#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

from autoresearch_helpers import (
    AutoresearchError,
    default_state_path,
    read_state_payload,
    read_runtime_payload,
    resolve_state_path,
    utc_now,
    write_json_atomic,
)
from autoresearch_launch_gate import pid_is_alive
from autoresearch_lessons import append_summary_lesson_if_needed, lessons_path_from_results


DEFAULT_RESULTS_PATH = "research-results.tsv"
DEFAULT_CODEX_ARGS = ["--full-auto"]
DEFAULT_HEALTH_MIN_FREE_MB = 500


def resolve_repo_path(repo_arg: str | None) -> Path:
    return Path(repo_arg or Path.cwd()).resolve()


def resolve_repo_relative(repo: Path, raw: str | None, default_path: Path) -> Path:
    if raw is None:
        return default_path
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = repo / candidate
    return candidate.resolve()


def parse_key_value_pairs(values: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise AutoresearchError(f"Expected KEY=VALUE, got: {value!r}")
        key, raw_value = value.split("=", 1)
        key = key.strip()
        if not key:
            raise AutoresearchError(f"Invalid empty key in: {value!r}")
        parsed[key] = raw_value.strip()
    return parsed


def load_runtime_if_exists(runtime_path: Path) -> dict[str, Any] | None:
    if not runtime_path.exists():
        return None
    return read_runtime_payload(runtime_path)


def load_runtime_with_error(runtime_path: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not runtime_path.exists():
        return None, None
    try:
        return read_runtime_payload(runtime_path), None
    except AutoresearchError as exc:
        return None, str(exc)


def ensure_runtime_not_running(runtime_path: Path) -> None:
    existing, runtime_error = load_runtime_with_error(runtime_path)
    if runtime_error is not None:
        raise AutoresearchError(runtime_error)
    if existing is not None and pid_is_alive(existing.get("pid")):
        raise AutoresearchError("An autoresearch runtime is already running for this repo.")


def persist_runtime(runtime_path: Path, payload: dict[str, Any]) -> None:
    payload = dict(payload)
    payload["updated_at"] = utc_now()
    write_json_atomic(runtime_path, payload)


def append_completion_summary_if_possible(
    *,
    results_path: Path,
    state_path: Path,
) -> None:
    if not results_path.exists() or not state_path.exists():
        return
    try:
        state_payload = read_state_payload(state_path)
        append_summary_lesson_if_needed(
            lessons_path=lessons_path_from_results(results_path),
            state_payload=state_payload,
            current_iteration=int(state_payload.get("state", {}).get("iteration", 0)),
        )
    except (AutoresearchError, OSError, ValueError, TypeError):
        return


def manifest_config_from_args(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "goal": args.goal,
        "scope": args.scope,
        "metric": args.metric_name,
        "direction": args.direction,
        "verify": args.verify,
        "guard": args.guard,
        "iterations": args.iterations,
        "run_tag": args.run_tag,
        "stop_condition": args.stop_condition,
        "rollback_policy": args.rollback_policy,
        "parallel_mode": args.parallel_mode,
        "web_search": args.web_search,
    }


def destructive_rollback_approved(launch_manifest: dict[str, Any]) -> bool:
    approvals = launch_manifest.get("approvals", {})
    if not isinstance(approvals, dict):
        return False
    for key in ("destructive_rollback", "rollback", "destructive"):
        value = approvals.get(key)
        if value in {True, "true", "yes", "approved", "allow"}:
            return True
    return False
