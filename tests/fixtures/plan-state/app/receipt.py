"""Receipt lines shown to the customer after checkout."""

from pricing import order_total


def receipt_lines(items, coupon=None):
    subtotal = sum(item["price"] * item["qty"] for item in items)
    lines = [f"{item['name']} x{item['qty']}" for item in items]
    if coupon == "SAVE10" and subtotal >= 100:
        lines.append("Знижка SAVE10: -10%")
        subtotal = subtotal * 0.9
    if subtotal >= 50:
        lines.append("Доставка: безкоштовно")
    else:
        lines.append("Доставка: 5")
    lines.append(f"Разом: {order_total(items, coupon)}")
    return lines
