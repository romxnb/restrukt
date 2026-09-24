import unittest

from pricing import order_total
from receipt import receipt_lines

KETTLE = {"name": "Чайник", "price": 120, "qty": 1}
CUPS = {"name": "Чашка", "price": 20, "qty": 2}


class ShopTests(unittest.TestCase):
    def test_coupon_discounts_large_order_with_free_shipping(self):
        self.assertEqual(order_total([KETTLE], "SAVE10"), 108.0)

    def test_coupon_ignored_for_small_order(self):
        self.assertEqual(order_total([CUPS], "SAVE10"), 45)

    def test_receipt_shows_discount_shipping_and_total(self):
        self.assertEqual(
            receipt_lines([KETTLE], "SAVE10"),
            ["Чайник x1", "Знижка SAVE10: -10%", "Доставка: безкоштовно", "Разом: 108.0"],
        )

    def test_receipt_for_small_order_charges_shipping(self):
        self.assertEqual(
            receipt_lines([CUPS]),
            ["Чашка x2", "Доставка: 5", "Разом: 45"],
        )


if __name__ == "__main__":
    unittest.main()
