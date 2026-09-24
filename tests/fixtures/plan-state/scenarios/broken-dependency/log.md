# Результати перебудови

## Знижка за купоном має одного власника

- Результат: `pricing.coupon_discount` — єдина умова `SAVE10`; `order_total` і `receipt_lines` рахують знижку через неї.
- Перевірено: `python3 -m unittest` → 4 тести OK.
