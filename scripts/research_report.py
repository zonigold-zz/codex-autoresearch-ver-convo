#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

def try_read_json(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

def try_read_tsv(path: Path):
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f, delimiter="\t"))
    except Exception:
        return []

def main() -> int:
    parser = argparse.ArgumentParser(description="Write a human-readable report from autoresearch artifacts.")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--output", default="reports/latest_run.md")
    args = parser.parse_args()

    repo_root = Path(args.repo).resolve()
    output_path = repo_root / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    state = try_read_json(repo_root / "autoresearch-state.json") or {}
    rows = try_read_tsv(repo_root / "research-results.tsv")
    latest = rows[-1] if rows else {}

    lines = [
        "# Latest autoresearch run",
        "",
        "## Overview",
        f"- Repo: `{repo_root}`",
        f"- Iterations recorded: `{len(rows)}`",
    ]

    if state:
        lines.append(f"- Run tag: `{state.get('run_tag', 'unknown')}`")
        lines.append(f"- Session mode: `{state.get('session_mode', 'unknown')}`")
        lines.append(f"- Best metric: `{state.get('best_metric', state.get('best_value', 'unknown'))}`")
    else:
        lines.append("- State file: not found or unreadable")

    lines.extend(["", "## Latest recorded row"])
    if latest:
        for key in ("iteration", "status", "metric", "metric_value", "decision", "summary"):
            if key in latest and latest[key]:
                lines.append(f"- {key}: `{latest[key]}`")
    else:
        lines.append("- No TSV rows found yet")

    lines.extend([
        "",
        "## Suggested next actions",
        "- Confirm the verify command and guard commands are still current.",
        "- Review whether the retained best result matches the intended mechanism/path.",
        "- If this run is research-facing, update `research/project.yaml` and `research/datasets.yaml` with any changed assumptions.",
        "",
    ])

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"written": str(output_path), "iterations": len(rows)}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
