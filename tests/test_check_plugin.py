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

    def test_status_must_forward_arguments(self):
        path = self.root / "commands/status.md"
        path.write_text(path.read_text().replace("$ARGUMENTS", ""))
        self.assertIn("commands/status.md: arguments are not forwarded", checker.check(self.root))

    def test_missing_tactical_method_breaks_its_consumers(self):
        (self.root / "skills/restrukt/methods/implementation.md").unlink()
        errors = checker.check(self.root)
        self.assertTrue(any("references/apply.md: broken link:" in e for e in errors))

    def test_missing_caller_check_breaks_apply_and_code_review(self):
        (self.root / "skills/restrukt/methods/caller-check.md").unlink()
        errors = checker.check(self.root)
        self.assertTrue(any("references/apply.md: broken link:" in e for e in errors))
        self.assertTrue(any("references/review-code.md: broken link:" in e for e in errors))

    def test_missing_handoff_check_breaks_plan_and_plan_review(self):
        (self.root / "skills/restrukt/references/handoff.md").unlink()
        errors = checker.check(self.root)
        self.assertTrue(any("references/plan.md: broken link:" in e for e in errors))
        self.assertTrue(any("references/review-plan.md: broken link:" in e for e in errors))

    def test_missing_task_rules_break_plan_and_implement(self):
        (self.root / "skills/restrukt/references/tasks.md").unlink()
        errors = checker.check(self.root)
        self.assertTrue(any("references/plan.md: broken link:" in e for e in errors))
        self.assertTrue(any("references/implement.md: broken link:" in e for e in errors))

    def test_missing_implement_reference_breaks_its_entry(self):
        (self.root / "skills/restrukt/references/implement.md").unlink()
        errors = checker.check(self.root)
        self.assertTrue(any("SKILL.md: broken link:" in e for e in errors))

    def test_missing_naming_principle_breaks_all_consumers(self):
        (self.root / "skills/restrukt/methods/naming.md").unlink()
        errors = checker.check(self.root)
        for consumer in ("references/apply.md", "references/plan.md", "references/review-code.md", "tools/names.md"):
            self.assertTrue(any(f"{consumer}: broken link:" in e for e in errors), consumer)

    def test_link_cycle_is_rejected(self):
        path = self.root / "skills/restrukt/references/review-code.md"
        path.write_text(path.read_text() + "\nСпільні умови — у [review](review.md).\n")
        errors = checker.check(self.root)
        self.assertTrue(any(e.startswith("Link cycle:") and "review-code.md" in e for e in errors))

    def test_template_task_states_must_match_contract(self):
        path = self.root / "skills/restrukt/templates/plan.md"
        path.write_text(path.read_text().replace("`готово`, `заблоковано", "`готово`, `перевірити`, `заблоковано"))
        self.assertIn(
            "skills/restrukt/templates/plan.md: task states differ from the contract",
            checker.check(self.root),
        )

    def test_template_whole_check_states_must_match_contract(self):
        path = self.root / "skills/restrukt/templates/plan.md"
        path.write_text(path.read_text().replace("`потребує виправлень`", "`є знахідки`"))
        self.assertIn(
            "skills/restrukt/templates/plan.md: whole-check states differ from the contract",
            checker.check(self.root),
        )

    def test_contract_must_own_state_legends(self):
        path = self.root / "skills/restrukt/SKILL.md"
        path.write_text(path.read_text().replace("## Стан плану", "## Стани"))
        errors = checker.check(self.root)
        self.assertTrue(any(e.startswith("skills/restrukt/SKILL.md: missing state legend") for e in errors))

    def test_manifest_versions_must_match(self):
        path = self.root / ".codex-plugin/plugin.json"
        data = json.loads(path.read_text())
        data["version"] = "99.0.0"
        path.write_text(json.dumps(data))
        self.assertIn("Plugin versions differ", checker.check(self.root))


if __name__ == "__main__":
    unittest.main()
