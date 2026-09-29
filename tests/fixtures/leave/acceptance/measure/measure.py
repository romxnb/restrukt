#!/usr/bin/env python3
"""Measure a leave-requests project against the hidden acceptance and code-quality checks.

usage: measure.py <project dir> <output dir> [--stream <stream.jsonl>] [--skip-e2e]
Writes <output dir>/measure.json and prints a one-line summary.
"""
import json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ACCEPTANCE = HERE.parent / "php"
E2E = HERE.parent / "e2e" / "run-e2e.sh"
EXCLUDED = re.compile(r"^(docs/|.*(composer|package-lock|symfony)\.(lock|json)$|backend/config/reference\.php$|backend/var/)")


def sh(command, cwd, env=None, timeout=900):
    merged = {**os.environ, **(env or {})}
    try:
        done = subprocess.run(command, cwd=cwd, shell=True, capture_output=True, text=True, env=merged, timeout=timeout)
        return done.returncode, done.stdout + done.stderr
    except subprocess.TimeoutExpired as error:
        return 124, f"timeout: {error}"


def first_json(text, opener):
    return json.JSONDecoder().raw_decode(text[text.index(opener):])[0]


def category(path):
    if path.startswith("backend/src/"):
        return "backend_src"
    if path.startswith("backend/tests/"):
        return "backend_tests"
    if path.startswith("backend/migrations/"):
        return "backend_migrations"
    if path.startswith("backend/"):
        return "backend_other"
    if path.startswith("frontend/src/") and re.search(r"(\.test\.ts$|\.spec\.ts$|__tests__/)", path):
        return "frontend_tests"
    if path.startswith("frontend/src/"):
        return "frontend_src"
    if path.startswith("frontend/"):
        return "frontend_other"
    return "other"


def diff_stats(project, base):
    sh("git add -A -N .", project)
    _, numstat = sh(f"git diff --numstat {base}", project)
    _, names = sh(f"git diff --name-status {base}", project)
    status = {}
    for line in names.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            status[parts[-1]] = parts[0][0]
    stats, files = {}, []
    for line in numstat.splitlines():
        added, deleted, path = line.split("\t", 2)
        if EXCLUDED.match(path) or added == "-":
            continue
        kind = category(path)
        entry = stats.setdefault(kind, {"added": 0, "deleted": 0, "files": 0, "new_files": 0})
        entry["added"] += int(added)
        entry["deleted"] += int(deleted)
        entry["files"] += 1
        if status.get(path) == "A":
            entry["new_files"] += 1
        files.append({"path": path, "added": int(added), "deleted": int(deleted), "status": status.get(path, "M")})
    return stats, files


def php_structure(project, paths):
    if not paths:
        return []
    _, out = sh("php " + str(HERE / "phpstructure.php") + " " + " ".join(paths), project / "backend")
    try:
        return first_json(out, "[")
    except ValueError:
        return []


def structure_summary(classes):
    interfaces = [c["name"] for c in classes if c["kind"] == "interface"]
    implementations = {name: [c["name"] for c in classes if name in c["implements"]] for name in interfaces}
    methods = [m for c in classes for m in c["methods"]]
    code_methods = [m for m in methods if m["lines"] > 0]
    single_public = [
        c["name"] for c in classes
        if c["kind"] == "class"
        and not c["extends"]
        and len([m for m in c["methods"] if m["visibility"] == "public" and m["name"] != "__construct" and not m["name"].startswith("__")]) == 1
    ]
    return {
        "types": {kind: sum(1 for c in classes if c["kind"] == kind) for kind in ("class", "interface", "enum", "trait")},
        "names": sorted(f'{c["kind"]} {c["namespace"]}\\{c["name"]}' for c in classes),
        "interfaces_with_one_implementation": sorted(n for n, impl in implementations.items() if len(impl) <= 1),
        "classes_with_one_public_method": sorted(single_public),
        "forwarding_methods": sorted(f'{c["name"]}::{m["name"]}' for c in classes for m in c["methods"] if m["forwarding"]),
        "methods": len(methods),
        "longest_methods": sorted(((m["lines"], f'{c["name"]}::{m["name"]}') for c in classes for m in c["methods"]), reverse=True)[:5],
        "methods_over_25_lines": sum(1 for m in code_methods if m["lines"] > 25),
    }


def new_php_files(files):
    return [f["path"].removeprefix("backend/") for f in files if f["path"].startswith("backend/src/") and f["path"].endswith(".php") and f["status"] == "A"]


def changed_php_files(files):
    return [f["path"].removeprefix("backend/") for f in files if f["path"].startswith("backend/src/") and f["path"].endswith(".php") and f["status"] != "D"]


def phpunit(project, target):
    junit = Path(tempfile.mkstemp(suffix=".xml")[1])
    code, out = sh(f"php bin/phpunit {target} --log-junit {junit}", project / "backend", timeout=1200)
    text = junit.read_text() if junit.exists() and junit.stat().st_size else ""
    junit.unlink(missing_ok=True)
    match = re.search(r'<testsuite name="[^"]*"[^>]*tests="(\d+)"[^>]*assertions="\d+"[^>]*errors="(\d+)"[^>]*failures="(\d+)"[^>]*skipped="(\d+)"', text)
    if not match:
        return {"exit": code, "tests": 0, "failed": None, "tail": out[-1500:]}
    tests, errors, failures, skipped = map(int, match.groups())
    failed_names = re.findall(r'<testcase name="([^"]+)"[^>]*class="([^"]+)"[^>]*>\s*<(?:failure|error)', text)
    return {"exit": code, "tests": tests, "failed": errors + failures, "skipped": skipped,
            "failed_tests": [f"{cls.split(chr(92))[-1]}::{name}" for name, cls in failed_names][:40]}


def hidden_acceptance(project):
    target = project / "backend/tests/Acceptance"
    shutil.rmtree(target, ignore_errors=True)
    shutil.copytree(ACCEPTANCE, target)
    try:
        return phpunit(project, "tests/Acceptance")
    finally:
        shutil.rmtree(target, ignore_errors=True)


def own_backend_tests(project):
    return phpunit(project, "")


def psalm(project):
    code, out = sh("vendor/bin/psalm --no-cache --output-format=json --no-progress", project / "backend", timeout=900)
    try:
        issues = first_json(out, "[")
    except ValueError:
        return {"exit": code, "errors": None, "tail": out[-800:]}
    errors = [i for i in issues if i.get("severity") == "error"]
    by_type = {}
    for issue in errors:
        by_type[issue["type"]] = by_type.get(issue["type"], 0) + 1
    return {"errors": len(errors), "by_type": by_type}


def cs_fixer(project):
    code, out = sh("vendor/bin/php-cs-fixer fix --dry-run --format=json", project / "backend")
    try:
        return {"files": len(first_json(out, "{")["files"])}
    except ValueError:
        return {"files": None, "tail": out[-500:]}


def migrations(project):
    with tempfile.TemporaryDirectory() as temp:
        env = {"DATABASE_URL": f"sqlite:///{temp}/migrate.db", "APP_ENV": "dev"}
        code, out = sh("php bin/console doctrine:migrations:migrate -n -q && php bin/console doctrine:schema:validate", project / "backend", env)
        return {"in_sync": code == 0, "tail": out[-400:] if code else ""}


def frontend(project):
    root = project / "frontend"
    result = {}
    code, out = sh("npx vitest run --reporter=json --outputFile=/tmp/vitest-measure.json", root, timeout=600)
    try:
        report = json.loads(Path("/tmp/vitest-measure.json").read_text())
        result["tests"] = {"tests": report["numTotalTests"], "failed": report["numFailedTests"]}
    except (OSError, ValueError, KeyError):
        result["tests"] = {"tests": 0, "failed": None, "tail": out[-500:]}
    code, out = sh("npx vue-tsc --noEmit", root, timeout=600)
    result["typecheck_errors"] = len(re.findall(r"error TS\d+", out))
    code, out = sh("npx eslint . -f json", root, timeout=600)
    try:
        report = first_json(out, "[")
        result["lint"] = {"errors": sum(f["errorCount"] for f in report), "warnings": sum(f["warningCount"] for f in report)}
    except ValueError:
        result["lint"] = {"errors": None, "tail": out[-500:]}
    code, out = sh("npx prettier --check src/", root)
    result["unformatted_files"] = len(re.findall(r"^\[warn\] (?!Code style)", out, re.M))
    return result


def frontend_structure(project, files):
    new = [f["path"] for f in files if f["path"].startswith("frontend/src/") and f["status"] == "A"]
    changed = [f["path"] for f in files if f["path"].startswith("frontend/src/") and f["status"] != "D"]
    text = {p: (project / p).read_text(errors="replace") for p in changed if (project / p).exists()}
    src = {p: t for p, t in text.items() if category(p) == "frontend_src"}
    return {
        "new_components": sorted(p for p in new if p.endswith(".vue")),
        "new_modules": sorted(p for p in new if p.endswith(".ts") and category(p) == "frontend_src"),
        "any": sum(len(re.findall(r":\s*any\b|as any\b|<any>", t)) for t in src.values()),
        "eslint_disable": sum(t.count("eslint-disable") for t in src.values()),
        "raw_fetch": sum(t.count("fetch(") for p, t in src.items() if not p.endswith("api/client.ts")),
        "largest_components": sorted(((t.count("\n"), p) for p, t in src.items() if p.endswith(".vue")), reverse=True)[:3],
    }


def run_stats(stream):
    """Plugin reads, process-document edits and cost; a stream may hold several sessions (plan, then apply steps)."""
    if not stream or not Path(stream).exists():
        return {}
    results, plugin_reads, docs_writes, agents = {}, 0, 0, 0
    for line in Path(stream).read_text().splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get("type") == "assistant":
            for block in event["message"].get("content", []):
                if block.get("type") != "tool_use":
                    continue
                data = block.get("input", {})
                if block["name"] == "Read" and "/skills/restrukt/" in data.get("file_path", ""):
                    plugin_reads += 1
                if block["name"] in ("Write", "Edit") and "/docs/restrukt/" in data.get("file_path", ""):
                    docs_writes += 1
                if block["name"] in ("Agent", "Task"):
                    agents += 1
        elif event.get("type") == "result":
            session = event.get("session_id")
            if session not in results or event.get("total_cost_usd", 0) >= results[session].get("total_cost_usd", 0):
                results[session] = event
    stats = {"plugin_reads": plugin_reads, "process_doc_edits": docs_writes, "subagents": agents, "sessions": len(results)}
    if results:
        stats.update(
            cost=round(sum(r.get("total_cost_usd", 0) for r in results.values()), 2),
            turns=sum(r.get("num_turns") or 0 for r in results.values()),
            minutes=round(sum(r.get("duration_ms", 0) for r in results.values()) / 60000, 1),
            error=any(r.get("is_error") for r in results.values()),
        )
    return stats


def main():
    project, out_dir = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    stream = sys.argv[sys.argv.index("--stream") + 1] if "--stream" in sys.argv else None
    out_dir.mkdir(parents=True, exist_ok=True)
    _, base = sh("git rev-list --max-parents=0 HEAD", project)
    base = base.split()[-1]
    stats, files = diff_stats(project, base)
    new_classes = php_structure(project, new_php_files(files))
    report = {
        "diff": stats,
        "files": files,
        "php_new": structure_summary(new_classes),
        "php_changed_files_structure": structure_summary(php_structure(project, changed_php_files(files))),
        "frontend_structure": frontend_structure(project, files),
        "hidden_acceptance": hidden_acceptance(project),
        "own_backend_tests": own_backend_tests(project),
        "psalm": psalm(project),
        "cs_fixer": cs_fixer(project),
        "migrations": migrations(project),
        "frontend": frontend(project),
        "run": run_stats(stream),
    }
    if "--skip-e2e" not in sys.argv:
        code, out = sh(f"{E2E} {project} {out_dir / 'e2e'}", project, timeout=900)
        passed = failed = 0
        try:
            e2e = json.loads((out_dir / "e2e/e2e-results.json").read_text())
            passed, failed = e2e["stats"]["expected"], e2e["stats"]["unexpected"]
        except (OSError, ValueError, KeyError):
            pass
        report["e2e"] = {"exit": code, "passed": passed, "failed": failed}
    (out_dir / "measure.json").write_text(json.dumps(report, ensure_ascii=False, indent=1))
    d = lambda k: stats.get(k, {}).get("added", 0)
    h = report["hidden_acceptance"]
    print(f"hidden {h.get('tests', 0) - (h.get('failed') or 0)}/{h.get('tests')} e2e {report.get('e2e', {}).get('passed')}/{2} "
          f"be_src +{d('backend_src')} be_tests +{d('backend_tests')} fe_src +{d('frontend_src')} fe_tests +{d('frontend_tests')} "
          f"php_types {report['php_new']['types']} psalm {report['psalm'].get('errors')} cs {report['cs_fixer'].get('files')} "
          f"tsc {report['frontend']['typecheck_errors']} lint {report['frontend']['lint']} cost {report['run'].get('cost')}")


if __name__ == "__main__":
    main()
