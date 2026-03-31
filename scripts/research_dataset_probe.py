#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

CANDIDATE_DIR_NAMES = {"data", "dataset", "datasets", "raw", "processed", "input", "inputs", "bids", "eeg", "edf"}
FILE_EXTENSIONS = {".csv", ".tsv", ".json", ".jsonl", ".parquet", ".npy", ".npz", ".mat", ".edf", ".bdf", ".fif", ".pt", ".pth", ".ckpt"}
IGNORE_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", "dist", "build", ".mypy_cache", ".pytest_cache"}

def walk_files(root: Path):
    for path in root.rglob("*"):
        if any(part in IGNORE_DIRS for part in path.parts):
            continue
        if path.is_file():
            yield path

def main() -> int:
    parser = argparse.ArgumentParser(description="Emit a lightweight JSON summary of research signals in a repo.")
    parser.add_argument("--repo", required=True)
    args = parser.parse_args()
    repo_root = Path(args.repo).resolve()

    candidate_dirs = []
    ext_counter = Counter()
    research_scripts = []
    notebooks = []

    for path in repo_root.rglob("*"):
        if not path.exists():
            continue
        if path.is_dir():
            if any(part in IGNORE_DIRS for part in path.parts):
                continue
            if path.name.lower() in CANDIDATE_DIR_NAMES:
                candidate_dirs.append(str(path.relative_to(repo_root)))

    for path in walk_files(repo_root):
        suffix = path.suffix.lower()
        rel = str(path.relative_to(repo_root))
        if suffix in FILE_EXTENSIONS:
            ext_counter[suffix] += 1
        lower_name = path.name.lower()
        if lower_name.endswith(".ipynb"):
            notebooks.append(rel)
        if lower_name.endswith(".py") and any(token in lower_name for token in ("train", "eval", "infer", "benchmark", "ablation")):
            research_scripts.append(rel)

    manifest_candidates = ["pyproject.toml", "requirements.txt", "environment.yml", "package.json", "Makefile"]
    manifests = [name for name in manifest_candidates if (repo_root / name).exists()]

    payload = {
        "repo": str(repo_root),
        "candidate_dirs": sorted(set(candidate_dirs))[:50],
        "manifests": manifests,
        "research_scripts": sorted(research_scripts)[:50],
        "notebooks": sorted(notebooks)[:50],
        "file_extension_counts": dict(sorted(ext_counter.items())),
    }
    print(json.dumps(payload, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
