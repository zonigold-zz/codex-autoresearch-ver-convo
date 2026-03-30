#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
from pathlib import Path

FILES = {
    "config.toml": ".codex/config.toml",
    "default.rules": ".codex/rules/default.rules",
}

def backup_if_needed(path: Path) -> str | None:
    if not path.exists():
        return None
    timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = path.with_name(f"{path.name}.bak.{timestamp}")
    shutil.copy2(path, backup)
    return str(backup)

def main() -> int:
    parser = argparse.ArgumentParser(description="Apply project-scoped Codex research defaults.")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--profile", default="research-safe")
    args = parser.parse_args()

    skill_root = Path(__file__).resolve().parent.parent
    template_root = skill_root / "templates" / "research"
    repo_root = Path(args.repo).resolve()

    result = {"repo": str(repo_root), "profile": args.profile, "files": {}}
    for src_name, rel_dst in FILES.items():
        src = template_root / src_name
        dst = repo_root / rel_dst
        dst.parent.mkdir(parents=True, exist_ok=True)
        backup = backup_if_needed(dst)
        shutil.copy2(src, dst)
        result["files"][rel_dst] = {"written": True, "backup": backup}

    print(json.dumps(result, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
