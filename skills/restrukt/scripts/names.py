#!/usr/bin/env python3
"""Show the names of a code scope side by side, so that inconsistency becomes visible.

Sections: words of identifiers with the names that use them; leading verbs of operations;
names grouped by the type of their value; candidates that often break a naming rule;
values without a name. Python files are parsed exactly; other languages are read
approximately with regular expressions. The script decides nothing: a candidate is a
question for the reader, and a name that passes the rules stays.
"""

import ast
import re
import signal
import sys
from collections import defaultdict
from pathlib import Path

SOURCE = {".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".go", ".java", ".kt", ".kts", ".cs",
          ".rs", ".swift", ".php", ".rb", ".scala", ".dart", ".vue", ".svelte"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", "target", "vendor",
             ".next", ".nuxt", "coverage", ".mypy_cache", ".pytest_cache", ".ruff_cache"}
KEYWORDS = set("""
if else elif for while do return def class function const let var import from export default new this self
true false null none undefined nil and or not in is async await try except catch finally raise throw with as
pass break continue lambda yield public private protected static void interface type enum struct impl fn pub mut
match case switch package func go defer chan map range select extends implements super instanceof typeof keyof
readonly abstract final override virtual namespace using del global nonlocal assert val when object companion
init constructor get set of where guard fileprivate internal open sealed data suspend lateinit module require
end begin unless until then elsif rescue ensure any string number boolean bool int float double char long
short byte void never unknown symbol bigint str list dict tuple print len
""".split())
VAGUE = {"data", "info", "stuff", "thing", "things", "obj", "object", "tmp", "temp", "val", "manager", "mgr",
         "helper", "helpers", "util", "utils", "misc", "common", "shared", "process", "do", "flag", "foo", "bar",
         "dummy"}
TYPE_WORDS = {"list", "dict", "map", "array", "arr", "str", "string", "obj", "int", "num", "set", "tuple"}
ABBREVIATIONS = {"amt", "qty", "cnt", "usr", "calc", "res", "nxt", "prv", "lst", "tbl", "cfg", "conf", "cb",
                 "idx", "addr", "acct", "cust", "emp", "pwd", "btn", "msg", "mgr", "impl", "svc", "repo", "util",
                 "proc", "desc", "num", "str", "val", "len", "attr", "elem", "evt", "dt", "ts"}
CONFUSABLE = {"l", "O", "I"}
SHORT_OK = {"_", "i", "j", "k", "n", "e"}
IDENTIFIER = re.compile(r"[A-Za-z_$][\w$]*")
CODE_STRING = re.compile(r"^[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+$|^[A-Z]{3,}$")
HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
TEST_PATH = re.compile(r"(^|/)(tests?|spec|__tests__)(/|$)|(^|/)test_[^/]*$|[._-](test|spec)\.[a-z]+$")
TEST_NAME = re.compile(r"^(test|it|should)(_|[A-Z]|$)")
LIMIT = 10


def words(identifier: str) -> list[str]:
    spaced = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", identifier.strip("_$"))
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", spaced)
    return [w.lower() for w in re.split(r"[_\s$]+", spaced) if w]


class Scope:
    def __init__(self) -> None:
        self.names: dict[str, set[str]] = defaultdict(set)      # identifier -> places
        self.tests: set[str] = set()
        self.operations: set[str] = set()
        self.typed: dict[str, set[str]] = defaultdict(set)      # type -> identifiers
        self.candidates: list[str] = []
        self.unnamed: list[str] = []
        self.codes: dict[str, set[str]] = defaultdict(set)      # code-like string -> places

    def add(self, name: str, place: str, operation: bool = False, value_type: str = "") -> None:
        if name.lower() in KEYWORDS or len(name) > 80:
            return
        if operation and TEST_NAME.match(name):
            self.tests.add(name)
            return
        self.names[name].add(place)
        if operation:
            self.operations.add(name)
        if value_type:
            self.typed[value_type].add(name)


def annotation(node: ast.AST | None) -> str:
    if node is None:
        return ""
    text = ast.unparse(node)
    text = re.sub(r"^Optional\[(.*)\]$", r"\1", text)
    return re.sub(r"\s*\|\s*None$", "", text)


def read_python(path: Path, place: str, scope: Scope) -> None:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return
    constant_lines: set[int] = set()
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if all(isinstance(t, ast.Name) and t.id.isupper() for t in targets):
                constant_lines.update(range(node.lineno, (node.end_lineno or node.lineno) + 1))
    in_tests = bool(TEST_PATH.search(place))
    for node in ast.walk(tree):
        at = f"{place}:{getattr(node, 'lineno', 0)}"
        if isinstance(node, ast.ClassDef):
            scope.add(node.name, at)
            bases = {ast.unparse(base).rsplit(".", 1)[-1] for base in node.bases}
            if any(b in ("Exception", "BaseException") or b.endswith(("Error", "Exception")) for b in bases) \
                    and not node.name.endswith(("Error", "Exception", "Warning", "Exit", "Interrupt")):
                scope.candidates.append(f"{at} `{node.name}` — виняток без суфікса `Error`")
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    scope.add(item.target.id, f"{place}:{item.lineno}", value_type=annotation(item.annotation))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            scope.add(node.name, at, operation=True)
            args = node.args
            for arg in args.posonlyargs + args.args + args.kwonlyargs + [args.vararg, args.kwarg]:
                if arg is not None and arg.arg not in ("self", "cls"):
                    scope.add(arg.arg, f"{place}:{arg.lineno}", value_type=annotation(arg.annotation))
        elif isinstance(node, ast.Lambda):
            for arg in node.args.args:
                scope.add(arg.arg, at)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            scope.add(node.id, at)
        elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store) \
                and isinstance(node.value, ast.Name) and node.value.id == "self":
            scope.add(node.attr, at)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            scope.add(node.name, at)
        elif isinstance(node, ast.Constant):
            value = node.value
            if isinstance(value, str) and CODE_STRING.match(value) and value not in HTTP_METHODS:
                scope.codes[value].add(at)
            elif isinstance(value, (int, float)) and not isinstance(value, bool) and value not in (0, 1, -1) \
                    and not (100 <= value < 600 and float(value).is_integer()) \
                    and node.lineno not in constant_lines and not in_tests:
                scope.unnamed.append(f"{at} {value!r}")


# Declarations in C-like languages, Go, Rust, Swift, Kotlin, PHP and Ruby; approximate by design.
DECLARATIONS = [
    (re.compile(r"\b(?:class|interface|type|enum|struct|trait|record|object|protocol)\s+([A-Za-z_$][\w$]*)"), False),
    (re.compile(r"\b(?:function\*?|fn|func|fun|def)\s+(?:\([^)]*\)\s*)?([A-Za-z_$][\w$]*[!?]?)"), True),
    (re.compile(r"\b(?:const|let|var|val)\s+([A-Za-z_$][\w$]*)\s*(?::[^=]+)?=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>"),
     True),
    (re.compile(r"^\s*(?:(?:public|private|protected|static|async|override|readonly|final|abstract|suspend)\s+)*"
                r"([A-Za-z_$][\w$]*)\s*\([^)]*\)\s*(?::\s*[^{;=]+)?\s*\{", re.M), True),
    (re.compile(r"\b(?:const|let|var|val)\s+([A-Za-z_$][\w$]*)"), False),
]
TYPED = re.compile(r"\b([A-Za-z_$][\w$]*)\??\s*:\s*(string|number|boolean|bigint|Date|[A-Z][\w$.]*(?:<[^<>;=]*>)?)"
                   r"(?:\s*\|\s*(?:null|undefined))?(?=\s*[,;)=\n}])")


def strip_literals(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    text = re.sub(r"(?m)(?<![:\"'])//.*$", " ", text)
    text = re.sub(r"(?m)^\s*#.*$", " ", text)
    return re.sub(r"`(?:\\.|[^`\\])*`|\"(?:\\.|[^\"\\\n])*\"|'(?:\\.|[^'\\\n])*'", '""', text)


def read_other(path: Path, place: str, scope: Scope) -> None:
    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return
    for code in re.findall(r"[\"'`]([A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+)[\"'`]", raw):
        scope.codes[code].add(place)
    if not TEST_PATH.search(place):
        for match in re.finditer(r"(?<![\w.$])(\d+\.\d+|[2-9]\d*|1\d+)(?![\w.])", strip_literals(raw)):
            line = raw.count("\n", 0, match.start()) + 1
            before = raw[raw.rfind("\n", 0, match.start()) + 1:match.start()]
            if not re.search(r"\b[A-Z][A-Z0-9_]*\s*[:=]\s*$|\b(const|static final)\b.*\b[A-Z][A-Z0-9_]*\b", before):
                scope.unnamed.append(f"{place}:{line} {match[1]}")
    text = strip_literals(raw)
    for pattern, operation in DECLARATIONS:
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            name = match[1]
            if name not in ("if", "for", "while", "switch", "catch", "function", "return"):
                scope.add(name, f"{place}:{line}", operation=operation)
    for match in TYPED.finditer(text):
        line = text.count("\n", 0, match.start()) + 1
        scope.add(match[1], f"{place}:{line}", value_type=match[2])


def candidates(scope: Scope) -> None:
    for name, places in sorted(scope.names.items()):
        where = sorted(places)[0]
        parts = words(name)
        reasons = []
        if name in CONFUSABLE:
            reasons.append("літеру легко сплутати з цифрою")
        elif len(name) == 1 and name not in SHORT_OK:
            reasons.append("одна літера: чи мала область видимості")
        if re.search(r"[A-Za-z]\d+$", name):
            reasons.append("номер у кінці")
        if len(parts) > 1 and set(parts) & TYPE_WORDS:
            reasons.append("тип у назві")
        if set(parts) & VAGUE:
            reasons.append("розмите слово: " + ", ".join(sorted(set(parts) & VAGUE)))
        if set(parts) & ABBREVIATIONS - VAGUE:
            reasons.append("скорочення: " + ", ".join(sorted(set(parts) & ABBREVIATIONS - VAGUE)))
        if reasons:
            scope.candidates.append(f"{where} `{name}` — " + "; ".join(reasons))


def show(title: str, rows: list[str]) -> None:
    print(f"\n## {title}\n")
    for row in rows or ["—"]:
        print(f"- {row}")


def listing(names: set[str] | list[str]) -> str:
    ordered = sorted(names)
    extra = f" … ще {len(ordered) - LIMIT}" if len(ordered) > LIMIT else ""
    return ", ".join(f"`{n}`" for n in ordered[:LIMIT]) + extra


def main(paths: list[str]) -> int:
    scope = Scope()
    files = []
    for argument in paths:
        root = Path(argument)
        found = [root] if root.is_file() else [
            p for p in root.rglob("*") if p.is_file() and not set(p.parts) & SKIP_DIRS]
        files += [p for p in found if p.suffix in SOURCE]
    for path in sorted(set(files)):
        (read_python if path.suffix == ".py" else read_other)(path, str(path), scope)
    candidates(scope)

    by_word: dict[str, set[str]] = defaultdict(set)
    for name in scope.names:
        for word in words(name):
            by_word[word].add(name)
    verbs: dict[str, set[str]] = defaultdict(set)
    for name in scope.operations:
        verbs[words(name)[0] if words(name) else name].add(name)
    files_of = {code: {place.rsplit(":", 1)[0] for place in places} for code, places in scope.codes.items()}
    repeated = [f"`{code}` у {len(files_of[code])} файлах: {', '.join(sorted(places)[:4])}"
                for code, places in sorted(scope.codes.items()) if len(files_of[code]) > 1]
    typed = [f"{t}: {listing(ns)}" for t, ns in sorted(scope.typed.items()) if t]

    # Short sections first: a reader who cuts the output still sees every kind of finding.
    print(f"# Назви: {' '.join(paths)} — файлів {len(set(files))}, назв {len(scope.names)}; "
          f"кандидатів {len(scope.candidates)}, значень без назви {len(scope.unnamed) + len(repeated)}, "
          f"типів {len(typed)}, перших слів операцій {len(verbs)}, тестів {len(scope.tests)}, слів {len(by_word)}")
    show("Кандидати: перевір за правилами", scope.candidates)
    show("Значення без назви: числа поза константами й коди рядками в кількох місцях", scope.unnamed + repeated)
    show("За типом значення: однакове названо за одним шаблоном", typed)
    show("Перше слово операцій: одне дієслово — один зміст",
         [f"{v} ×{len(ns)}: {listing(ns)}" for v, ns in sorted(verbs.items(), key=lambda i: (-len(i[1]), i[0]))])
    show("Назви тестів: кожна каже, яку поведінку перевіряє", sorted(scope.tests))
    show("Слова: синоніми одного поняття й одне слово для різних",
         [f"{w} ×{len(ns)}: {listing(ns)}" for w, ns in sorted(by_word.items(), key=lambda i: (-len(i[1]), i[0]))])
    print("\nКандидат — питання, а не вирок: змінюй лише назву, що порушує правило методики.")
    return 0


if __name__ == "__main__":
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # quiet when the reader cuts the output with head
    if len(sys.argv) < 2:
        print("usage: names.py <file or directory> [...]")
        sys.exit(2)
    sys.exit(main(sys.argv[1:]))
