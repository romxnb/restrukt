"""Order pricing for the shop checkout."""


def coupon_discount(amount, coupon):
    if coupon == "SAVE10" and amount >= 100:
        return amount * 0.9
    return amount


def order_total(items, coupon=None):
    subtotal = coupon_discount(sum(item["price"] * item["qty"] for item in items), coupon)
    shipping = 0 if subtotal >= 50 else 5
    return round(subtotal + shipping, 2)
