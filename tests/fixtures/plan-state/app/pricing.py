"""Order pricing for the shop checkout."""


def order_total(items, coupon=None):
    subtotal = sum(item["price"] * item["qty"] for item in items)
    if coupon == "SAVE10" and subtotal >= 100:
        subtotal = subtotal * 0.9
    shipping = 0 if subtotal >= 50 else 5
    return round(subtotal + shipping, 2)
