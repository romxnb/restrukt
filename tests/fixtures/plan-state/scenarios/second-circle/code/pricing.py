"""Order pricing for the shop checkout."""


def subtotal(items):
    return sum(item["price"] * item["qty"] for item in items)


def coupon_discount(amount, coupon):
    if coupon == "SAVE10" and amount >= 100:
        return amount * 0.9
    return amount


def shipping_cost(amount):
    return 0 if amount >= 50 else 5


def order_total(items, coupon=None):
    discounted = coupon_discount(subtotal(items), coupon)
    return round(discounted + shipping_cost(discounted), 2)
