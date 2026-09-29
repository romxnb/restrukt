#!/usr/bin/env python3
"""Create a fresh copy of the leave app for one run.

usage: prepare.py <base|reference|messy> <new dir> [--deps <prepared copy>]

base — the app without the feature (implement the spec); reference — the feature written by hand;
messy — the feature written badly (rewrite it). The copy is a new git repository with one commit.
--deps hardlinks backend/vendor and frontend/node_modules from an earlier copy instead of installing them.
"""

import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def run(command: list[str], cwd: Path) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def main() -> None:
    variant, target = sys.argv[1], Path(sys.argv[2]).resolve()
    if variant not in ("base", "reference", "messy") or target.exists():
        sys.exit(__doc__)
    shutil.copytree(HERE / "app", target)
    if variant != "base":
        run(["git", "apply", str(HERE / "variants" / f"{variant}.patch")], target)

    if "--deps" in sys.argv:
        source = Path(sys.argv[sys.argv.index("--deps") + 1]).resolve()
        run(["cp", "-al", str(source / "backend/vendor"), str(target / "backend/vendor")], target)
        run(["cp", "-al", str(source / "frontend/node_modules"), str(target / "frontend/node_modules")], target)
    else:
        run(["composer", "install", "--no-interaction"], target / "backend")
        run(["npm", "ci", "--no-audit", "--no-fund"], target / "frontend")

    run(["git", "init", "-q", "-b", "main"], target)
    run(["git", "add", "-A"], target)
    run(["git", "-c", "user.name=dev", "-c", "user.email=dev@example.com", "commit", "-qm", "Базовий стан"], target)
    print(f"{variant} → {target}")


if __name__ == "__main__":
    main()
