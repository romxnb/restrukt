"""Regression checks for the names inventory the naming method relies on."""

import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "skills/restrukt/scripts/names.py"


def inventory(files: dict[str, str]) -> str:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        for relative, body in files.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(textwrap.dedent(body), encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), str(root)], capture_output=True, text=True, check=True,
        )
        return completed.stdout.replace(str(root) + "/", "")


def section(report: str, title: str) -> str:
    start = report.index(f"## {title}")
    end = report.find("\n## ", start + 1)
    return report[start:end if end != -1 else None]


PYTHON = {
    "shop/models.py": """
        from dataclasses import dataclass
        from datetime import date

        @dataclass
        class Order:
            id: int
            created: date
            shipped_on: date
            paid: bool = False
    """,
    "shop/repo.py": """
        LIMIT = 30

        def get_order(orders, order_id):
            return orders.get(order_id)

        def fetch_customer(customers, customer_id):
            return [l for l in customers if l.id == customer_id]

        def late_fee(days):
            if days > 14:
                return days * 0.2
            return "OUT_OF_STOCK"
    """,
    "shop/messages.py": """
        MESSAGES = {"OUT_OF_STOCK": "Немає на складі"}
    """,
    "shop/errors.py": """
        class Refused(Exception):
            pass

        class OutOfStockError(Exception):
            pass
    """,
    "tests/test_shop.py": """
        def test_1():
            assert late_fee(20) == 4.0

        def test_order_over_limit_is_rejected():
            assert True
    """,
}


class PythonInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = inventory(PYTHON)

    def test_same_type_names_stand_together(self):
        by_type = section(self.report, "За типом значення")
        self.assertIn("date: `created`, `shipped_on`", by_type)
        self.assertIn("bool: `paid`", by_type)

    def test_operations_are_grouped_by_leading_verb(self):
        verbs = section(self.report, "Перше слово операцій")
        self.assertIn("get ×1: `get_order`", verbs)
        self.assertIn("fetch ×1: `fetch_customer`", verbs)

    def test_confusable_letter_is_a_candidate(self):
        self.assertIn("`l` — літеру легко сплутати з цифрою", section(self.report, "Кандидати"))

    def test_exception_without_error_suffix_is_a_candidate(self):
        candidates = section(self.report, "Кандидати")
        self.assertIn("`Refused` — виняток без суфікса `Error`", candidates)
        self.assertNotIn("`OutOfStockError`", candidates)

    def test_unnamed_numbers_and_shared_codes_are_listed(self):
        unnamed = section(self.report, "Значення без назви")
        self.assertRegex(unnamed, r"shop/repo\.py:\d+ 14\n")
        self.assertRegex(unnamed, r"shop/repo\.py:\d+ 0\.2\n")
        self.assertNotIn(" 30", unnamed)
        self.assertNotIn("test_shop.py", unnamed)
        self.assertIn("`OUT_OF_STOCK` у 2 файлах", unnamed)

    def test_test_names_are_listed_apart_from_words(self):
        self.assertIn("- test_1", section(self.report, "Назви тестів"))
        self.assertNotIn("test ×", section(self.report, "Слова"))


class ApproximateInventoryTests(unittest.TestCase):
    def test_typescript_declarations_and_types(self):
        report = inventory({
            "web/orders.ts": """
                interface Order { createdAt: Date; shippedOn: Date; }
                export class OrderManager {}
                export async function fetchOrder(id: string) { return null; }
                const loadCustomer = async (id: string) => null;
                const retry = 3;
                // const hidden = 7;
            """,
        })
        self.assertIn("Date: `createdAt`, `shippedOn`", section(report, "За типом значення"))
        verbs = section(report, "Перше слово операцій")
        self.assertIn("`fetchOrder`", verbs)
        self.assertIn("`loadCustomer`", verbs)
        self.assertIn("розмите слово: manager", section(report, "Кандидати"))
        self.assertNotIn("hidden", report)

    def test_php_numbers_keep_their_lines_and_skip_statuses_and_constants(self):
        report = inventory({
            "src/Shipping.php": """
                <?php
                /**
                 * Delivery rules.
                 */
                final class Shipping
                {
                    private const FREE_FROM = 50;

                    public function price(int $total): JsonResponse
                    {
                        $label = "Доставка за 7 днів";
                        if ($total > 30) {
                            return new JsonResponse(['price' => 0], 200);
                        }
                        return new JsonResponse(['error' => 'Замало'], 422);
                    }
                }
            """,
        })
        unnamed = section(report, "Значення без назви")
        self.assertIn("src/Shipping.php:13 30", unnamed)
        self.assertNotIn(" 50", unnamed)
        self.assertNotIn(" 7", unnamed)
        self.assertNotIn(" 200", unnamed)
        self.assertNotIn(" 422", unnamed)

    def test_vue_styles_are_not_code(self):
        report = inventory({
            "src/Card.vue": """
                <script setup lang="ts">
                const retries = 3
                </script>

                <style scoped>
                .card { z-index: 10; margin: 12px; }
                </style>
            """,
        })
        unnamed = section(report, "Значення без назви")
        self.assertIn("src/Card.vue:3 3", unnamed)
        self.assertNotIn(" 10", unnamed)
        self.assertNotIn(" 12", unnamed)


if __name__ == "__main__":
    unittest.main()
