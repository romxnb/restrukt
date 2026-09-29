#!/usr/bin/env python3
"""Measure behaviour and names of a naming-fixture project after a run.

Usage: check.py <project> [--task renewals] [--json <file>]

The report has the same sections for every run:
- the project's own tests;
- the wire contract of the mobile API, driven only through `library.web.dispatch`;
- with --task, the task's acceptance through the same API;
- identifiers: planted defects that remain, words used for one concept, lookup verbs,
  vague words and abbreviations, test names, numeric literals outside named constants;
- ruff and pyright findings when the tools are installed.

Names are compared with the base commit, so a run on the clean base lists the
identifiers the run introduced.
"""

import argparse
import ast
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

# The mobile client depends on these routes, fields and texts; any run must keep them.
CONTRACT = r'''
import json
from datetime import date
from library.app import App
from library.web import dispatch


class Calendar:
    def __init__(self, today):
        self.today = today

    def __call__(self):
        return self.today


calendar = Calendar(date(2026, 3, 2))
app = App(calendar)
results = []


def expect(name, method, path, body, status, fields):
    actual_status, actual_body = dispatch(app, method, path, body)
    ok = actual_status == status and all(
        actual_body.get(key) == value if value is not ... else key in actual_body
        for key, value in fields.items()
    )
    results.append({"name": name, "ok": ok, "status": actual_status, "body": actual_body})
    return actual_body


expect("add book", "POST", "/books", {"isbn": "111", "title": "Кобзар", "author": "Тарас Шевченко"},
       201, {"isbn": "111"})
expect("add copies", "POST", "/books",
       {"isbn": "222", "title": "Лісова пісня", "author": "Леся Українка", "copies": 3}, 201, {})
expect("add book 333", "POST", "/books", {"isbn": "333", "title": "Тигролови", "author": "Іван Багряний"}, 201, {})
expect("add book 444", "POST", "/books", {"isbn": "444", "title": "Місто", "author": "Валер'ян Підмогильний"}, 201, {})
for member_id in (1, 2, 3):
    expect(f"register {member_id}", "POST", "/members",
           {"user_id": member_id, "name": f"member {member_id}", "email": f"{member_id}@example.com"},
           200, {"user_id": member_id, "fines": "0.00"})
first = expect("lend", "POST", "/loans", {"user_id": 1, "isbn": "111"}, 201, {"loan_id": ..., "due": "2026-03-16"})
expect("no free copy", "POST", "/loans", {"user_id": 2, "isbn": "111"}, 409, {"error": "Усі примірники зараз видано."})
expect("place hold", "POST", "/holds", {"user_id": 2, "isbn": "111"}, 201, {"hold_id": ...})
expect("hold twice", "POST", "/holds", {"user_id": 2, "isbn": "111"}, 409, {"error": "Ви вже забронювали цю книжку."})
calendar.today = date(2026, 3, 26)
expect("late return", "POST", "/returns", {"loan_id": first.get("loan_id")}, 200, {"fine": "2.50"})
expect("return twice", "POST", "/returns", {"loan_id": first.get("loan_id")}, 404, {"error": "Видачу не знайдено."})
expect("held for another", "POST", "/loans", {"user_id": 3, "isbn": "111"}, 409,
       {"error": "Книжку заброньовано іншим читачем."})
second = expect("first in queue", "POST", "/loans", {"user_id": 2, "isbn": "111"}, 201, {"due": "2026-04-09"})
expect("hold by 3", "POST", "/holds", {"user_id": 3, "isbn": "111"}, 201, {})
expect("return on time", "POST", "/returns", {"loan_id": second.get("loan_id")}, 200, {"fine": "0.00"})
expect("staff out of turn", "POST", "/loans", {"user_id": 1, "isbn": "111", "staff": True}, 201, {})
expect("unknown member", "POST", "/loans", {"user_id": 42, "isbn": "222"}, 409, {"error": "Читача не знайдено."})
expect("unknown book", "POST", "/loans", {"user_id": 3, "isbn": "999"}, 409,
       {"error": "Такої книжки немає в каталозі."})
for isbn in ("222", "333", "444"):
    expect(f"lend {isbn}", "POST", "/loans", {"user_id": 3, "isbn": isbn}, 201, {})
expect("too many loans", "POST", "/loans", {"user_id": 3, "isbn": "111"}, 409,
       {"error": "У вас уже три книжки. Поверніть одну, щоб узяти нову."})
late = expect("lend for cap", "POST", "/loans", {"user_id": 2, "isbn": "222"}, 201, {})
calendar.today = date(2026, 7, 1)
expect("capped fine", "POST", "/returns", {"loan_id": late.get("loan_id")}, 200, {"fine": "10.00"})
expect("fines shown", "POST", "/members", {"user_id": 2}, 200, {"user_id": 2, "fines": "10.00"})
expect("unpaid fines", "POST", "/loans", {"user_id": 2, "isbn": "222"}, 409, {"error": "Спершу сплатіть штраф."})
expect("unknown loan", "POST", "/returns", {"loan_id": 999}, 404, {"error": "Видачу не знайдено."})
expect("unknown route", "POST", "/nowhere", {}, 404, {"error": "not found"})
print(json.dumps(results, ensure_ascii=False, default=str))
'''

# Acceptance of tasks/renewals.md through the API; refusal texts are the implementer's choice.
RENEWALS = r'''
import json
from datetime import date
from library.app import App
from library.web import dispatch


class Calendar:
    def __init__(self, today):
        self.today = today

    def __call__(self):
        return self.today


results = []


def library():
    calendar = Calendar(date(2026, 3, 2))
    app = App(calendar)
    for isbn, copies in (("111", 1), ("222", 3)):
        dispatch(app, "POST", "/books", {"isbn": isbn, "title": isbn, "author": "a", "copies": copies})
    for member_id in (1, 2, 3):
        dispatch(app, "POST", "/members", {"user_id": member_id, "name": "m", "email": "m@example.com"})
    return app, calendar


def expect(app, name, path, body, status, fields=None):
    actual_status, actual_body = dispatch(app, "POST", path, body)
    fields = fields or {}
    ok = actual_status == status and all(actual_body.get(k) == v for k, v in fields.items())
    if status == 409:
        ok = ok and isinstance(actual_body.get("error"), str) and bool(actual_body["error"].strip())
    results.append({"name": name, "ok": ok, "status": actual_status, "body": actual_body})
    return actual_body


app, calendar = library()
loan = expect(app, "lend", "/loans", {"user_id": 1, "isbn": "111"}, 201)
expect(app, "renew once", "/renewals", {"loan_id": loan.get("loan_id")}, 200, {"due": "2026-03-30"})
expect(app, "renew twice", "/renewals", {"loan_id": loan.get("loan_id")}, 200, {"due": "2026-04-13"})
expect(app, "third renewal", "/renewals", {"loan_id": loan.get("loan_id")}, 409)

app, calendar = library()
loan = expect(app, "lend", "/loans", {"user_id": 1, "isbn": "111"}, 201)
calendar.today = date(2026, 3, 17)
expect(app, "overdue loan", "/renewals", {"loan_id": loan.get("loan_id")}, 409)
calendar.today = date(2026, 3, 16)
expect(app, "due today", "/renewals", {"loan_id": loan.get("loan_id")}, 200, {"due": "2026-03-30"})

app, calendar = library()
loan = expect(app, "lend", "/loans", {"user_id": 1, "isbn": "111"}, 201)
expect(app, "hold by another", "/holds", {"user_id": 2, "isbn": "111"}, 201)
expect(app, "held for another", "/renewals", {"loan_id": loan.get("loan_id")}, 409)

app, calendar = library()
first = expect(app, "lend first", "/loans", {"user_id": 1, "isbn": "111"}, 201)
calendar.today = date(2026, 5, 25)
second = expect(app, "lend second", "/loans", {"user_id": 1, "isbn": "222"}, 201)
calendar.today = date(2026, 6, 1)
expect(app, "capped fine", "/returns", {"loan_id": first.get("loan_id")}, 200, {"fine": "10.00"})
expect(app, "unpaid fines", "/renewals", {"loan_id": second.get("loan_id")}, 409)
expect(app, "unknown loan", "/renewals", {"loan_id": 999}, 404, {"error": "Видачу не знайдено."})
expect(app, "returned loan", "/renewals", {"loan_id": first.get("loan_id")}, 404, {"error": "Видачу не знайдено."})

app, calendar = library()
loan = expect(app, "lend", "/loans", {"user_id": 1, "isbn": "111"}, 201)
calendar.today = date(2026, 3, 26)
expect(app, "late return", "/returns", {"loan_id": loan.get("loan_id")}, 200, {"fine": "2.50"})
expect(app, "part payment", "/payments", {"user_id": 1, "amount": "1.00"}, 200, {"fines": "1.50"})
expect(app, "zero payment", "/payments", {"user_id": 1, "amount": "0.00"}, 409)
expect(app, "negative payment", "/payments", {"user_id": 1, "amount": "-1.00"}, 409)
expect(app, "overpayment", "/payments", {"user_id": 1, "amount": "5.00"}, 409)
expect(app, "full payment", "/payments", {"user_id": 1, "amount": "1.50"}, 200, {"fines": "0.00"})
expect(app, "unknown member pays", "/payments", {"user_id": 42, "amount": "1.00"}, 404)

app, calendar = library()
loan = expect(app, "lend", "/loans", {"user_id": 1, "isbn": "111"}, 201)
calendar.today = date(2026, 7, 1)
expect(app, "capped fine", "/returns", {"loan_id": loan.get("loan_id")}, 200, {"fine": "10.00"})
expect(app, "blocked", "/loans", {"user_id": 1, "isbn": "222"}, 409)
expect(app, "pay half", "/payments", {"user_id": 1, "amount": "5.00"}, 200, {"fines": "5.00"})
expect(app, "borrow after paying", "/loans", {"user_id": 1, "isbn": "222"}, 201)
print(json.dumps(results, ensure_ascii=False, default=str))
'''

TASKS = {"renewals": RENEWALS}

# Planted in bases/legacy: the identifier, then what a reader gets wrong.
PLANTED = {
    "helpers": "module name says nothing about the lending rules inside",
    "User": "synonym of member",
    "Reservation": "synonym of hold",
    "PatronService": "synonym of member; suffix without meaning",
    "LoanMgr": "abbreviation; manager says nothing",
    "Beacon": "metaphor for the mailer",
    "ping": "metaphor for sending a letter",
    "get_patron": "get that registers a member",
    "get_user": "synonym of member; one of four lookup verbs",
    "add_user": "synonym of member",
    "fetch_book": "one of four lookup verbs",
    "retrieve_loan": "one of four lookup verbs",
    "load_reservations": "lookup verb; returns only the active queue in order",
    "loans_for": "returns only active loans",
    "process": "vague verb for lending",
    "do_return": "noise prefix",
    "reserve": "synonym of placing a hold",
    "handle_reserve": "synonym of placing a hold",
    "calc": "says nothing: counts overdue days",
    "calc_fine": "abbreviation",
    "check_limit": "also checks fines and returns a reason",
    "err2": "numbered vague name of the refusal response",
    "fines_amt": "abbreviation; plural for one amount",
    "borrower_id": "synonym of member",
    "patron_id": "synonym of member",
    "client_id": "synonym of member",
    "patrons": "synonym of member",
    "uid": "abbreviation; synonym of member",
    "start": "which start: the day the book was borrowed",
    "returned": "reads as a flag, holds a date",
    "res": "abbreviation used for both reservations and results",
    "beacon": "metaphor for the mailer",
    "data": "vague: the book",
    "loans_list": "type in the name",
    "lst": "type in the name",
    "tmp": "vague: the new loan",
    "q": "vague: the hold queue",
    "nxt": "abbreviation: the next hold",
    "flag": "vague: lend out of turn",
    "obj": "vague: the stored record",
    "msg_code": "abbreviation",
    "x": "vague: overdue days",
    "f": "vague: fine",
    "d1": "vague date",
    "d2": "vague date",
    "u": "single letter in a long scope",
    "b": "single letter in a long scope",
    "l": "ambiguous letter l",
    "mk": "abbreviation: builds a library",
    "a": "single letter: the app under test",
    "T": "test case class without meaning",
    "test_1": "test name without behaviour",
    "test_2": "test name without behaviour",
    "test_fine2": "numbered test name",
    "test_it_works": "test name without behaviour",
    "test_dup": "abbreviation",
}

# Words of one concept; one concept should keep one word in code.
CONCEPTS = {
    "member": {"member", "members", "user", "users", "uid", "patron", "patrons", "borrower", "client", "reader",
               "customer"},
    "hold": {"hold", "holds", "reservation", "reservations", "reserve", "res"},
    "lookup verb (storage)": {"get", "fetch", "retrieve", "load", "find", "lookup"},
}

VAGUE = {"data", "info", "tmp", "temp", "obj", "val", "stuff", "thing", "manager", "mgr", "helper", "helpers",
         "util", "utils", "misc", "flag", "lst", "dict", "list", "amt", "qty", "cnt", "calc", "nxt", "num",
         "str", "do", "process", "result", "res", "ret"}

TYPE_SUFFIX = re.compile(r"_(list|dict|str|int|obj|set|map)$")
TEST_NAME = re.compile(r"^test_?(\d+|it_works|works|ok|basic|dup|\w{1,4})$")


@dataclass
class Name:
    name: str
    kind: str
    file: str
    line: int


def words(identifier: str) -> list[str]:
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", identifier.strip("_"))
    return [w.lower() for w in re.split(r"[_\s]+", spaced) if w]


def names_in(node: ast.AST, scope: str, relative: str, in_tests: bool, found: list[Name]) -> None:
    for child in ast.iter_child_nodes(node):
        if isinstance(child, ast.ClassDef):
            found.append(Name(child.name, "class", relative, child.lineno))
            names_in(child, "class", relative, in_tests, found)
            continue
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            kind = "test" if in_tests and child.name.startswith("test") else (
                "method" if scope == "class" else "function")
            found.append(Name(child.name, kind, relative, child.lineno))
            args = child.args
            for arg in args.posonlyargs + args.args + args.kwonlyargs + [args.vararg, args.kwarg]:
                if arg is not None and arg.arg not in ("self", "cls"):
                    found.append(Name(arg.arg, "parameter", relative, arg.lineno))
            names_in(child, "function", relative, in_tests, found)
            continue
        if isinstance(child, ast.Lambda):
            for arg in child.args.args:
                found.append(Name(arg.arg, "parameter", relative, child.lineno))
        targets: list[ast.AST] = []
        if isinstance(child, ast.Assign):
            targets = child.targets
        elif isinstance(child, (ast.AnnAssign, ast.AugAssign)):
            targets = [child.target]
        elif isinstance(child, (ast.For, ast.comprehension)):
            targets = [child.target]
        elif isinstance(child, ast.withitem) and child.optional_vars is not None:
            targets = [child.optional_vars]
        elif isinstance(child, ast.ExceptHandler) and child.name:
            found.append(Name(child.name, "variable", relative, child.lineno))
        for target in targets:
            for leaf in ast.walk(target):
                if isinstance(leaf, ast.Name) and isinstance(leaf.ctx, ast.Store):
                    if scope == "module" and leaf.id.isupper():
                        kind = "constant"
                    elif scope == "class":
                        kind = "field"
                    else:
                        kind = "variable"
                    found.append(Name(leaf.id, kind, relative, getattr(leaf, "lineno", 0)))
                elif (isinstance(leaf, ast.Attribute) and isinstance(leaf.ctx, ast.Store)
                      and isinstance(leaf.value, ast.Name) and leaf.value.id == "self"):
                    found.append(Name(leaf.attr, "attribute", relative, leaf.lineno))
        names_in(child, scope, relative, in_tests, found)


def inventory(root: Path) -> list[Name]:
    found: list[Name] = []
    for path in sorted(root.rglob("*.py")):
        relative = path.relative_to(root)
        if relative.parts[0] not in ("library", "tests"):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as error:
            found.append(Name(f"<syntax error: {error}>", "error", str(relative), 0))
            continue
        if path.stem != "__init__":
            found.append(Name(path.stem, "module", str(relative), 1))
        names_in(tree, "module", str(relative), relative.parts[0] == "tests", found)
    unique = {(n.name, n.kind, n.file): n for n in found}
    return list(unique.values())


def numeric_literals(root: Path) -> list[str]:
    """Numbers in library code outside NAMED = constants, apart from 0, 1 and HTTP statuses."""
    found = []
    for path in sorted((root / "library").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        constant_lines = set()
        for node in tree.body:
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                if all(isinstance(t, ast.Name) and t.id.isupper() for t in targets):
                    constant_lines.update(range(node.lineno, (node.end_lineno or node.lineno) + 1))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) \
                    and not isinstance(node.value, bool):
                if node.lineno in constant_lines or node.value in (0, 1, -1):
                    continue
                if 100 <= node.value < 600 and path.name == "web.py":
                    continue
                found.append(f"{path.relative_to(root)}:{node.lineno} {node.value!r}")
            if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "Decimal" and node.args \
                    and isinstance(node.args[0], ast.Constant) and node.lineno not in constant_lines:
                value = node.args[0].value
                if isinstance(value, str) and value not in ("0", "0.00", "0.0"):
                    found.append(f"{path.relative_to(root)}:{node.lineno} Decimal({value!r})")
    return found


def run_script(root: Path, script: str) -> list[dict] | str:
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as handle:
        handle.write(script)
    try:
        completed = subprocess.run(
            [sys.executable, handle.name], cwd=root, capture_output=True, text=True, timeout=120,
            env={**os.environ, "PYTHONPATH": str(root), "PYTHONDONTWRITEBYTECODE": "1"},
        )
    finally:
        os.unlink(handle.name)
    if completed.returncode != 0:
        return (completed.stderr or completed.stdout).strip().splitlines()[-1]
    return json.loads(completed.stdout.strip().splitlines()[-1])


def own_tests(root: Path) -> str:
    completed = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."],
        cwd=root, capture_output=True, text=True, timeout=300,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    lines = [line for line in completed.stderr.splitlines() if line.startswith(("Ran ", "OK", "FAILED"))]
    return " ".join(lines) or completed.stderr.strip()[-300:]


def lint(root: Path) -> dict[str, int | str]:
    counts: dict[str, int | str] = {}
    if shutil.which("ruff"):
        completed = subprocess.run(
            ["ruff", "check", "--select", "E,F,W,N,B,UP,SIM,RET,PL", "--ignore", "PLR2004,PLR0913,PLC0415",
             "--line-length", "120", "--output-format", "concise", "--no-cache", "library", "tests"],
            cwd=root, capture_output=True, text=True,
        )
        findings = [line for line in completed.stdout.splitlines() if re.match(r"^\S+:\d+:\d+: ", line)]
        counts["ruff"] = len(findings)
        counts["ruff rules"] = ", ".join(sorted({line.split(": ")[1].split()[0] for line in findings}))
    if shutil.which("pyright"):
        completed = subprocess.run(["pyright", "library"], cwd=root, capture_output=True, text=True)
        match = re.search(r"(\d+) errors?", completed.stdout)
        counts["pyright errors"] = int(match[1]) if match else completed.stdout.strip()[-200:]
    return counts


def base_inventory(root: Path) -> list[Name]:
    first = subprocess.run(["git", "rev-list", "--max-parents=0", "HEAD"], cwd=root, capture_output=True,
                           text=True).stdout.split()
    if not first:
        return []
    with tempfile.TemporaryDirectory() as temp:
        subprocess.run(["git", "worktree", "add", "-q", "--detach", temp, first[0]], cwd=root, check=True,
                       capture_output=True)
        try:
            return inventory(Path(temp))
        finally:
            subprocess.run(["git", "worktree", "remove", "--force", temp], cwd=root, capture_output=True)


def report(root: Path, task: str | None) -> dict:
    names = inventory(root)
    before = base_inventory(root)
    before_keys = {(n.name, n.kind) for n in before}
    new = [n for n in names if (n.name, n.kind) not in before_keys]
    present = {n.name for n in names}

    concepts = {}
    for concept, vocabulary in CONCEPTS.items():
        usage: dict[str, list[str]] = {}
        for n in names:
            candidates = words(n.name)
            if concept.startswith("lookup"):
                if n.kind != "method" or not n.file.startswith("library/"):
                    continue
                candidates = candidates[:1]
            for word in candidates:
                if word in vocabulary:
                    usage.setdefault(word, []).append(n.name)
        concepts[concept] = {word: sorted(set(found)) for word, found in sorted(usage.items())}

    suspicious = sorted({
        f"{n.name} ({n.kind}, {n.file})" for n in names
        if n.kind not in ("test",) and (
            set(words(n.name)) & VAGUE
            or TYPE_SUFFIX.search(n.name)
            or (len(n.name) == 1 and n.kind not in ("parameter",) and n.name not in ("_", "i", "j", "n"))
            or re.search(r"\d$", n.name)
        )
    })
    tests = sorted(n.name for n in names if n.kind == "test")
    result = {
        "project": str(root),
        "own tests": own_tests(root),
        "contract": run_script(root, CONTRACT),
        "planted remaining": {name: why for name, why in PLANTED.items() if name in present},
        "concept words": concepts,
        "suspicious names": suspicious,
        "test names": tests,
        "vague test names": [t for t in tests if TEST_NAME.match(t)],
        "numbers outside constants": numeric_literals(root),
        "new names": sorted({f"{n.kind} {n.name} ({n.file})" for n in new}),
        "lint": lint(root),
    }
    if task:
        result["task"] = run_script(root, TASKS[task])
    return result


def summary(result: dict) -> str:
    def failures(checks):
        if isinstance(checks, str):
            return f"did not run: {checks}"
        failed = [c for c in checks if not c["ok"]]
        return f"{len(checks) - len(failed)}/{len(checks)} ok" + (
            "; failed: " + "; ".join(f"{c['name']} -> {c['status']} {c['body']}" for c in failed) if failed else "")

    lines = [
        f"project: {result['project']}",
        f"own tests: {result['own tests']}",
        f"contract: {failures(result['contract'])}",
    ]
    if "task" in result:
        lines.append(f"task: {failures(result['task'])}")
    planted = result["planted remaining"]
    lines.append(f"planted defects remaining: {len(planted)}/{len(PLANTED)}")
    lines += [f"  {name}: {why}" for name, why in planted.items()]
    lines.append("concept words:")
    for concept, usage in result["concept words"].items():
        lines.append(f"  {concept}: " + "; ".join(f"{w} x{len(ids)} {ids[:6]}" for w, ids in usage.items()))
    lines.append(f"suspicious names ({len(result['suspicious names'])}):")
    lines += [f"  {s}" for s in result["suspicious names"]]
    lines.append(f"vague test names: {result['vague test names']}")
    lines.append(f"numbers outside constants ({len(result['numbers outside constants'])}): "
                 f"{result['numbers outside constants']}")
    lines.append(f"lint: {result['lint']}")
    lines.append(f"new names ({len(result['new names'])}):")
    lines += [f"  {s}" for s in result["new names"]]
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("project", type=Path)
    parser.add_argument("--task", choices=sorted(TASKS))
    parser.add_argument("--json", type=Path)
    options = parser.parse_args()
    outcome = report(options.project.resolve(), options.task)
    if options.json:
        options.json.write_text(json.dumps(outcome, ensure_ascii=False, indent=2), encoding="utf-8")
    print(summary(outcome))
