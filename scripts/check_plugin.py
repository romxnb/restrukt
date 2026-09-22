#!/usr/bin/env python3
"""Check package wiring and local documentation links without loading an agent."""

import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit


def check(root: Path) -> list[str]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    def manifest(relative: str) -> dict:
        try:
            value = json.loads((root / relative).read_text(encoding="utf-8"))
            if not isinstance(value, dict):
                raise ValueError("expected an object")
            return value
        except (OSError, ValueError) as error:
            errors.append(f"{relative}: {error}")
            return {}

    claude = manifest(".claude-plugin/plugin.json")
    codex = manifest(".codex-plugin/plugin.json")
    marketplace = manifest(".claude-plugin/marketplace.json")
    for label, data in (("Claude Code", claude), ("Codex", codex)):
        require(data.get("name") == "restrukt", f"{label}: wrong plugin name")
        require(bool(data.get("description")), f"{label}: missing description")
        version = data.get("version", "")
        require(
            isinstance(version, str)
            and re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][\w.-]+)?", version) is not None,
            f"{label}: invalid version",
        )
    require(claude.get("version") == codex.get("version"), "Plugin versions differ")

    skills = codex.get("skills")
    require(
        isinstance(skills, str) and (root / skills / "restrukt/SKILL.md").is_file(),
        "Codex: skills path does not resolve to restrukt",
    )
    plugins = marketplace.get("plugins", [])
    entries = [
        item for item in plugins
        if isinstance(item, dict) and item.get("name") == "restrukt"
    ] if isinstance(plugins, list) else []
    require(len(entries) == 1, "Marketplace must contain one restrukt entry")
    if len(entries) == 1:
        source = entries[0].get("source")
        require(
            isinstance(source, str) and (root / source).resolve() == root.resolve(),
            "Marketplace source must resolve to this plugin",
        )

    def frontmatter(relative: str, expected_name: str | None = None) -> str:
        path = root / relative
        if not path.is_file():
            errors.append(f"Missing entry point: {relative}")
            return ""
        body = path.read_text(encoding="utf-8")
        match = re.match(r"\A---\n(.*?)\n---\n", body, flags=re.S)
        if not match:
            errors.append(f"{relative}: missing frontmatter")
            return body
        fields = dict(re.findall(r"^([\w-]+):\s*(.*)$", match[1], flags=re.M))
        require(bool(fields.get("description")), f"{relative}: missing description")
        if expected_name:
            require(fields.get("name") == expected_name, f"{relative}: wrong name")
        return body

    skill = frontmatter("skills/restrukt/SKILL.md", "restrukt")
    for mode in ("run", "plan", "apply", "loop", "step", "refine", "status"):
        relative = f"commands/{mode}.md"
        body = frontmatter(relative)
        require(f"`{mode}`" in body, f"{relative}: wrong mode routing")
        require("${CLAUDE_PLUGIN_ROOT}/skills/restrukt/SKILL.md" in body, f"{relative}: missing skill entry")
        if mode != "status":
            require("$ARGUMENTS" in body, f"{relative}: arguments are not forwarded")
        require(f"/restrukt:{mode}" in skill, f"Skill does not expose {mode}")
    for path in sorted((root / "agents").glob("*.md")):
        frontmatter(str(path.relative_to(root)), path.stem)

    # The Ralph loop runs one step per session, so its runner must stay executable.
    runner = root / "scripts/restrukt_loop.sh"
    require(runner.is_file(), "Missing loop runner: scripts/restrukt_loop.sh")
    if runner.is_file():
        require(runner.stat().st_mode & 0o111 != 0, "Loop runner is not executable")
        require(
            "restrukt_loop.sh" in (root / "skills/restrukt/references/loop.md").read_text(encoding="utf-8"),
            "Loop reference does not name the runner",
        )

    # Resolve Markdown links; external links and same-document anchors need no file lookup.
    documents = [root / "README.md"]
    for directory in ("skills", "agents", "commands", "tests"):
        documents.extend((root / directory).rglob("*.md"))
    for path in documents:
        if not path.is_file():
            errors.append(f"Missing document: {path.relative_to(root)}")
            continue
        body = path.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^\]\n]*\]\(([^)\n]+)\)", body):
            target = target.strip().strip("<>")
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            destination = (path.parent / unquote(parsed.path)).resolve()
            require(destination.is_relative_to(root.resolve()), f"{path.relative_to(root)}: link leaves plugin: {target}")
            require(destination.exists(), f"{path.relative_to(root)}: broken link: {target}")

    return errors


if __name__ == "__main__":
    plugin_root = (
        Path(sys.argv[1]).resolve() if len(sys.argv) > 1
        else Path(__file__).resolve().parents[1]
    )
    failures = check(plugin_root)
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        sys.exit(1)
    print("PASS: manifests, entry points, command routing, loop runner and local links")
    print("Agent behavior and generated code quality require acceptance runs.")
