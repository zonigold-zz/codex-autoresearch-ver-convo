#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

TEMPLATE_NAMES = ("project.yaml", "datasets.yaml", "permissions.yaml")

def copy_text_no_bom(src: Path, dst: Path, force: bool) -> str:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and not force:
        return "skipped"
    text = src.read_text(encoding="utf-8-sig")
    dst.write_text(text, encoding="utf-8", newline="\n")
    return "written"

def main() -> int:
    parser = argparse.ArgumentParser(description="Seed repo-local research defaults from skill templates.")
    parser.add_argument("--repo", required=True, help="Target repository root")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    args = parser.parse_args()

    skill_root = Path(__file__).resolve().parent.parent
    template_root = skill_root / "templates" / "research"
    repo_root = Path(args.repo).resolve()

    result = {"repo": str(repo_root), "files": {}}
    for name in TEMPLATE_NAMES:
        src = template_root / name
        dst = repo_root / "research" / name
        result["files"][str(dst.relative_to(repo_root))] = copy_text_no_bom(src, dst, args.force)

    (repo_root / "reports").mkdir(parents=True, exist_ok=True)
    result["files"]["reports/"] = "ensured"
    print(json.dumps(result, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
