#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from decimal import Decimal
from pathlib import Path
from typing import Any

from autoresearch_artifacts import compare_summary_to_state, log_summary, parse_results_log, read_state_payload
from autoresearch_core import AutoresearchError, format_decimal


KEEP_GATE_MISS_RE = re.compile(r"\s*\[KEEP-GATE miss\].*$", re.IGNORECASE)
SUBJECT_HELDOUT_RE = re.compile(r"\bsubject[- ]heldout\b", re.IGNORECASE)
READ_ONLY_RE = re.compile(r"\b(read[- ]only|immutable)\b", re.IGNORECASE)
CONFIG_DRIVEN_SCORES_RE = re.compile(
    r"\b(config-defined scores?|subject score assignments?|hardcoded score map)\b",
    re.IGNORECASE,
)


def first_non_empty(*values: Any) -> str:
    for value in values:
        if isinstance(value, str):
            text = value.strip()
            if text:
                return text
    return ""


def infer_direction_words(direction: str) -> str:
    if direction == "higher":
        return "higher is better"
    if direction == "lower":
        return "lower is better"
    return "direction unspecified"


def safe_format_metric(value: Any) -> str:
    try:
        return format_decimal(Decimal(str(value)))
    except Exception:
        return str(value)


def clean_description(text: str) -> str:
    cleaned = text.strip()
    if cleaned.lower().startswith("[labels:"):
        closing = cleaned.find("]")
        if closing != -1:
            cleaned = cleaned[closing + 1 :].strip()
    cleaned = KEEP_GATE_MISS_RE.sub("", cleaned).strip()
    return cleaned.rstrip(".")


def split_change_fragments(text: str) -> list[str]:
    fragments = [text.strip(" .")]
    for splitter in ("; ", ". "):
        next_fragments: list[str] = []
        for fragment in fragments:
            pieces = [piece.strip(" .") for piece in fragment.split(splitter) if piece.strip(" .")]
            next_fragments.extend(pieces or [fragment])
        fragments = next_fragments

    expanded: list[str] = []
    for fragment in fragments:
        if " and made " in fragment:
            left, right = fragment.split(" and made ", 1)
            expanded.append(left.strip(" ."))
            expanded.append(f"Made {right.strip(' .')}")
            continue
        if " and updated " in fragment:
            left, right = fragment.split(" and updated ", 1)
            expanded.append(left.strip(" ."))
            expanded.append(f"Updated {right.strip(' .')}")
            continue
        expanded.append(fragment)
    return [fragment for fragment in expanded if fragment]


def dataset_paths_from_scope(scope: str) -> list[str]:
    candidates: list[str] = []
    for piece in scope.split(","):
        item = piece.strip()
        if not item:
            continue
        lowered = item.lower()
        if "/data/" in lowered or lowered.startswith("data/") or lowered.endswith((".csv", ".tsv", ".jsonl", ".parquet")):
            candidates.append(item)
    return candidates


def infer_split_policy(goal: str, descriptions: list[str]) -> str:
    haystacks = [goal, *descriptions]
    for text in haystacks:
        match = SUBJECT_HELDOUT_RE.search(text)
        if match:
            return match.group(0)
    return ""


def infer_raw_data_mutability(goal: str, descriptions: list[str]) -> str:
    haystacks = [goal, *descriptions]
    for text in haystacks:
        match = READ_ONLY_RE.search(text)
        if match:
            return match.group(0)
    if any("data/" in text.lower() for text in descriptions):
        return "unspecified"
    return ""


def load_artifacts(repo_root: Path) -> tuple[Any, dict[str, Any] | None, dict[str, Any], list[str]]:
    results_path = repo_root / "research-results.tsv"
    parsed = parse_results_log(results_path)
    warnings: list[str] = []

    state_payload: dict[str, Any] | None = None
    state_path = repo_root / "autoresearch-state.json"
    try:
        state_payload = read_state_payload(state_path)
    except AutoresearchError as exc:
        warnings.append(str(exc))

    config = dict(parsed.metadata)
    if state_payload is not None:
        for key, value in state_payload.get("config", {}).items():
            config[key] = value

    state_summary = state_payload.get("state", {}) if state_payload else {}
    if state_payload is not None:
        direction = first_non_empty(config.get("direction"), config.get("metric_direction"))
        if direction in {"higher", "lower"}:
            try:
                reconstructed = log_summary(parsed, direction)
            except AutoresearchError as exc:
                warnings.append(str(exc))
            else:
                mismatches = compare_summary_to_state(reconstructed, state_payload)
                if mismatches:
                    warnings.extend(f"State/TSV mismatch: {item}" for item in mismatches)

    return parsed, state_payload, config, warnings


def best_row(parsed: Any, state_payload: dict[str, Any] | None) -> Any:
    best_iteration = None
    if state_payload is not None:
        best_iteration = state_payload.get("state", {}).get("best_iteration")
    if isinstance(best_iteration, int):
        for row in parsed.main_rows:
            if row.main_iteration == best_iteration:
                return row
    for row in reversed(parsed.main_rows):
        if row.status == "keep":
            return row
    return parsed.main_rows[0]


def build_objective(config: dict[str, Any]) -> list[str]:
    goal = first_non_empty(config.get("goal"))
    if goal:
        return [goal]
    return ["Objective was not recorded in the run artifacts."]


def build_metric_and_verification(config: dict[str, Any], state_payload: dict[str, Any] | None) -> list[str]:
    metric = first_non_empty(config.get("metric"))
    direction = first_non_empty(config.get("direction"), config.get("metric_direction"))
    verify = first_non_empty(config.get("verify"))
    lines: list[str] = []
    if metric:
        lines.append(f"Metric: `{metric}` ({infer_direction_words(direction)})")
    else:
        lines.append("Metric: not recorded")
    if verify:
        lines.append(f"Verification command: `{verify}`")
    else:
        lines.append("Verification command: not recorded")
    if state_payload is not None:
        state = state_payload.get("state", {})
        lines.append(
            "Recorded progress: baseline "
            f"`{safe_format_metric(state.get('baseline_metric', '?'))}`"
            f" -> current `{safe_format_metric(state.get('current_metric', '?'))}`"
            f" across `{state.get('iteration', 0)}` completed iterations"
        )
    return lines


def build_dataset_section(config: dict[str, Any], parsed: Any) -> list[str]:
    scope = first_non_empty(config.get("scope"))
    descriptions = [clean_description(row.description) for row in parsed.main_rows]
    dataset_paths = dataset_paths_from_scope(scope)
    split_policy = infer_split_policy(first_non_empty(config.get("goal")), descriptions)
    raw_data_mutability = infer_raw_data_mutability(first_non_empty(config.get("goal")), descriptions)

    lines: list[str] = []
    if dataset_paths:
        lines.append("Dataset-related paths in declared scope: " + ", ".join(f"`{path}`" for path in dataset_paths))
    else:
        lines.append("Dataset paths: not explicitly declared in run scope")
    if split_policy:
        lines.append(f"Split assumption mentioned in artifacts: `{split_policy}`")
    else:
        lines.append("Split assumption: not explicitly recorded")
    if raw_data_mutability:
        lines.append(f"Raw-data mutability assumption: `{raw_data_mutability}`")
    elif dataset_paths:
        lines.append("Raw-data mutability assumption: not explicitly recorded")
    return lines


def build_guard_section(config: dict[str, Any], parsed: Any) -> list[str]:
    guards = config.get("guards")
    if not isinstance(guards, list):
        guard_text = first_non_empty(config.get("guard"), parsed.metadata.get("guards"), parsed.metadata.get("guard"))
        if guard_text:
            guards = [item.strip() for item in guard_text.split(";") if item.strip()]
        else:
            guards = []

    lines: list[str] = []
    if guards:
        for index, guard in enumerate(guards, start=1):
            lines.append(f"Guard {index}: `{guard}`")
    else:
        lines.append("No explicit guard commands were recorded.")

    dataset_paths = dataset_paths_from_scope(first_non_empty(config.get("scope")))
    kept_descriptions = [clean_description(row.description) for row in parsed.main_rows if row.status == "keep"]
    if dataset_paths and kept_descriptions:
        lines.append(
            "Retained change descriptions focus on code/config paths rather than direct dataset edits: "
            + ", ".join(f"`{path}`" for path in dataset_paths)
        )
    return lines


def build_best_result_section(parsed: Any, state_payload: dict[str, Any] | None) -> list[str]:
    best = best_row(parsed, state_payload)
    state = state_payload.get("state", {}) if state_payload else {}
    baseline = parsed.main_rows[0]

    lines = [
        f"Baseline metric: `{safe_format_metric(state.get('baseline_metric', baseline.metric))}`",
        f"Best retained metric: `{safe_format_metric(state.get('best_metric', best.metric))}`",
        f"Best iteration: `{state.get('best_iteration', best.main_iteration)}`",
        f"Retained commit: `{state.get('last_commit', best.commit) if best.status == 'keep' else best.commit}`",
    ]
    description = clean_description(best.description)
    if description:
        lines.append(f"Best retained change summary: {description}.")
    return lines


def build_key_changes_section(parsed: Any) -> list[str]:
    changes: list[str] = []
    for row in parsed.main_rows[1:]:
        description = clean_description(row.description)
        if not description:
            continue
        fragments = split_change_fragments(description)
        if row.status == "keep" and len(fragments) > 1:
            changes.extend(fragment + "." for fragment in fragments)
        else:
            prefix = f"Iteration {row.iteration} (`{row.status}`, metric `{safe_format_metric(row.metric)}`): "
            changes.append(prefix + description + ".")
    if not changes:
        return ["No post-baseline changes were recorded."]
    deduped: list[str] = []
    seen: set[str] = set()
    for change in changes:
        if change not in seen:
            seen.add(change)
            deduped.append(change)
    return deduped


def build_open_blockers_section(parsed: Any, state_payload: dict[str, Any] | None, warnings: list[str]) -> list[str]:
    blockers: list[str] = []
    state = state_payload.get("state", {}) if state_payload else {}
    descriptions = [clean_description(row.description) for row in parsed.main_rows]

    if CONFIG_DRIVEN_SCORES_RE.search(" ".join(descriptions)):
        blockers.append(
            "Current evaluation path appears to depend on config-provided subject scores rather than model-produced predictions."
        )
    if state.get("blocked", 0):
        blockers.append(f"Run recorded `{state['blocked']}` blocked iterations that may need manual follow-up.")
    if warnings:
        blockers.extend(warnings)
    if not blockers:
        return ["No explicit blockers were recorded in the run artifacts."]
    return blockers


def build_next_actions_section(parsed: Any, config: dict[str, Any]) -> list[str]:
    descriptions = [clean_description(row.description) for row in parsed.main_rows]
    actions: list[str] = []

    if CONFIG_DRIVEN_SCORES_RE.search(" ".join(descriptions)):
        actions.append(
            "Decide whether the config-driven score path is a deliberate stub or only a temporary evaluator shim, then document that choice in the experiment config."
        )
        actions.append(
            "If the goal is a real training path, replace the score table with model-produced predictions while preserving the current verify and guard commands."
        )

    dataset_paths = dataset_paths_from_scope(first_non_empty(config.get("scope")))
    if dataset_paths:
        actions.append(
            "Keep dataset integrity constraints explicit in future runs, especially for "
            + ", ".join(f"`{path}`" for path in dataset_paths)
            + "."
        )

    if not actions:
        actions.append("Run another iteration only after confirming that the verify and guard commands still reflect the intended research claim.")
    return actions


def render_section(title: str, bullets: list[str]) -> list[str]:
    lines = [f"## {title}", ""]
    for bullet in bullets:
        lines.append(f"- {bullet}")
    lines.append("")
    return lines


def write_report(repo_root: Path, output_path: Path) -> dict[str, Any]:
    parsed, state_payload, config, warnings = load_artifacts(repo_root)
    output_lines: list[str] = ["# Latest autoresearch run", ""]

    output_lines.extend(render_section("Objective", build_objective(config)))
    output_lines.extend(render_section("Metric and verification", build_metric_and_verification(config, state_payload)))
    output_lines.extend(render_section("Dataset and split assumptions", build_dataset_section(config, parsed)))
    output_lines.extend(render_section("Guards and safety constraints", build_guard_section(config, parsed)))
    output_lines.extend(render_section("Best retained result", build_best_result_section(parsed, state_payload)))
    output_lines.extend(render_section("Key changes tried", build_key_changes_section(parsed)))
    output_lines.extend(render_section("Open blockers", build_open_blockers_section(parsed, state_payload, warnings)))
    output_lines.extend(render_section("Recommended next actions", build_next_actions_section(parsed, config)))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(output_lines).rstrip() + "\n", encoding="utf-8", newline="\n")
    return {
        "written": str(output_path),
        "iterations": len(parsed.main_rows) - 1,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Write a researcher-friendly report from autoresearch artifacts.")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--output", default="reports/latest_run.md")
    args = parser.parse_args()

    repo_root = Path(args.repo).resolve()
    output_path = repo_root / args.output
    result = write_report(repo_root, output_path)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
