#!/usr/bin/env python3
"""Assemble a disposable project for one plan-state scenario."""

import shutil
import subprocess
import sys
from pathlib import Path

FIXTURE = Path(__file__).resolve().parent
SCENARIOS = FIXTURE / "scenarios"


def commit(project: Path, message: str) -> None:
    subprocess.run(["git", "add", "-A"], cwd=project, check=True)
    subprocess.run(
        ["git", "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid",
         "commit", "-q", "-m", message],
        cwd=project, check=True,
    )


def prepare(scenario: str, project: Path) -> None:
    source = SCENARIOS / scenario
    if not source.is_dir():
        known = ", ".join(sorted(p.name for p in SCENARIOS.iterdir() if p.is_dir()))
        raise SystemExit(f"Unknown scenario {scenario!r}; known: {known}")
    if project.exists():
        raise SystemExit(f"Destination already exists: {project}")

    shutil.copytree(FIXTURE / "app", project, ignore=shutil.ignore_patterns("__pycache__"))
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    commit(project, "основа")
    if (source / "code").is_dir():
        shutil.copytree(source / "code", project, dirs_exist_ok=True)
        commit(project, "виконані задачі")

    # Plans are working documents: like in a user's repository they stay uncommitted.
    plan_dir = project / "docs/restrukt/shop"
    plan_dir.mkdir(parents=True)
    for name in ("plan.md", "log.md"):
        shutil.copyfile(source / name, plan_dir / name)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: prepare.py <scenario> <new project directory>")
    prepare(sys.argv[1], Path(sys.argv[2]).resolve())
