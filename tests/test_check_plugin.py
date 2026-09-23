"""Regression checks for the package interface and dependency links."""

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("check_plugin", ROOT / "scripts/check_plugin.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class PackageContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "plugin"
        shutil.copytree(
            ROOT, self.root,
            ignore=shutil.ignore_patterns(".git", "__pycache__", ".DS_Store"),
        )

    def test_current_package_is_valid(self):
        self.assertEqual(checker.check(self.root), [])

    def test_missing_review_entry_is_rejected(self):
        (self.root / "commands/review.md").unlink()
        errors = checker.check(self.root)
        self.assertTrue(any("Missing entry point: commands/review.md" in e for e in errors))

    def test_unsupported_command_is_rejected(self):
        shutil.copyfile(
            self.root / "commands/plan.md",
            self.root / "commands/obsolete.md",
        )
        self.assertIn("Command set must match supported modes", checker.check(self.root))

    def test_review_cannot_route_to_another_mode(self):
        path = self.root / "commands/review.md"
        path.write_text(path.read_text().replace("`review`", "`apply`"))
        self.assertIn("commands/review.md: wrong mode routing", checker.check(self.root))

    def test_missing_tactical_method_breaks_its_consumers(self):
        (self.root / "skills/restrukt/methods/implementation.md").unlink()
        errors = checker.check(self.root)
        self.assertTrue(any("references/apply.md: broken link:" in e for e in errors))
        self.assertTrue(any("references/review.md: broken link:" in e for e in errors))

    def test_manifest_versions_must_match(self):
        path = self.root / ".codex-plugin/plugin.json"
        data = json.loads(path.read_text())
        data["version"] = "99.0.0"
        path.write_text(json.dumps(data))
        self.assertIn("Plugin versions differ", checker.check(self.root))


if __name__ == "__main__":
    unittest.main()
