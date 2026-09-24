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
    modes = {"plan", "implement", "apply", "review", "refine", "status"}
    command_names = {path.stem for path in (root / "commands").glob("*.md")}
    require(command_names == modes, "Command set must match supported modes")
    for mode in sorted(modes):
        relative = f"commands/{mode}.md"
        body = frontmatter(relative)
        require(f"`{mode}`" in body, f"{relative}: wrong mode routing")
        require("${CLAUDE_PLUGIN_ROOT}/skills/restrukt/SKILL.md" in body, f"{relative}: missing skill entry")
        if mode != "status":
            require("$ARGUMENTS" in body, f"{relative}: arguments are not forwarded")
        require(f"/restrukt:{mode}" in skill, f"Skill does not expose {mode}")
    for path in sorted((root / "agents").glob("*.md")):
        frontmatter(str(path.relative_to(root)), path.stem)

    # The plan template repeats the contract's state legends so a plan explains itself; copies must not drift.
    def state_legend(relative: str, body: str, heading: str, label: str) -> list[str]:
        section = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", body, flags=re.M | re.S)
        sentence = section and re.search(rf"^{re.escape(label)}(.*?)\.(?:\s|$)", section[1], flags=re.M)
        if not sentence:
            errors.append(f"{relative}: missing state legend {label!r} in section {heading!r}")
            return []
        return re.findall(r"`([^`]+)`", sentence[1])

    template_path = "skills/restrukt/templates/plan.md"
    template = (root / template_path).read_text(encoding="utf-8") if (root / template_path).is_file() else ""
    for contract_label, template_heading, template_label, states in (
        ("Задача:", "Задачі", "Стани:", "task states"),
        ("«Перевірка цілого»:", "Перевірка цілого", "Стан:", "whole-check states"),
    ):
        expected = state_legend("skills/restrukt/SKILL.md", skill, "Стан плану", contract_label)
        actual = state_legend(template_path, template, template_heading, template_label)
        require(
            not expected or not actual or expected == actual,
            f"{template_path}: {states} differ from the contract",
        )

    # Resolve Markdown links; external links and same-document anchors need no file lookup.
    documents = [root / "README.md"]
    links: dict[Path, set[Path]] = {}
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
            if destination.suffix == ".md" and destination.is_file() and destination != path.resolve():
                links.setdefault(path.resolve(), set()).add(destination)

    # Agents read documents top-down; a link cycle hides which file owns a rule.
    done: set[Path] = set()

    def find_cycle(node: Path, trail: list[Path]) -> None:
        if node in trail:
            cycle = trail[trail.index(node):] + [node]
            errors.append("Link cycle: " + " -> ".join(str(p.relative_to(root.resolve())) for p in cycle))
            return
        if node in done:
            return
        for nxt in sorted(links.get(node, ())):
            find_cycle(nxt, trail + [node])
        done.add(node)

    for start in sorted(links):
        find_cycle(start, [])

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
    print("PASS: manifests, entry points, command routing and local links")
    print("Agent behavior and generated code quality require acceptance runs.")
