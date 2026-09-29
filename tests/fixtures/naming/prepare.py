#!/usr/bin/env python3
"""Assemble a disposable project from one base of the naming fixture."""

import shutil
import subprocess
import sys
from pathlib import Path

BASES = Path(__file__).resolve().parent / "bases"


def prepare(base: str, project: Path) -> None:
    source = BASES / base
    if not source.is_dir():
        known = ", ".join(sorted(p.name for p in BASES.iterdir() if p.is_dir()))
        raise SystemExit(f"Unknown base {base!r}; known: {known}")
    if project.exists():
        raise SystemExit(f"Destination already exists: {project}")

    shutil.copytree(source, project, ignore=shutil.ignore_patterns("__pycache__"))
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    subprocess.run(["git", "add", "-A"], cwd=project, check=True)
    subprocess.run(
        ["git", "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid",
         "commit", "-q", "-m", "основа"],
        cwd=project, check=True,
    )


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: prepare.py <legacy|clean> <new project directory>")
    prepare(sys.argv[1], Path(sys.argv[2]).resolve())
