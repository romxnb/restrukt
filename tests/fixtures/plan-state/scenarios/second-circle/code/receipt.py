"""Receipt lines shown to the customer after checkout."""

from pricing import coupon_discount, order_total, shipping_cost, subtotal


def receipt_lines(items, coupon=None):
    amount = subtotal(items)
    discounted = coupon_discount(amount, coupon)
    lines = [f"{item['name']} x{item['qty']}" for item in items]
    if discounted != amount:
        lines.append("Знижка SAVE10: -10%")
    cost = shipping_cost(discounted)
    lines.append("Доставка: безкоштовно" if cost == 0 else f"Доставка: {cost}")
    lines.append(f"Разом: {order_total(items, coupon)}")
    return lines
