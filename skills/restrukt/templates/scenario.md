# S1 · Покупець оформлює замовлення

контекст [C1a](../C1a.md) · точка входу `Checkout.submit@Checkout.ts:40` · звірка: 2 з 4 кроків = · orchestration home: немає → C1a.4a · рядки плану: C1a.1, C1a.2, C1a.7

## To-be

Текст приймання: builder звіряє з ним тіло orchestration home крок за кроком.

1. Покупець оформлює кошик → «замовлення оформлено» (`orderPlaced`)
2. коли замовлення оформлено, тоді → J1
3. магазин списує оплату → «оплату проведено» (`paymentCaptured`, через `PaymentPort`) ⇢ C2
4. замовлення йде на склад (`Warehouse.receive`)

## As-is

1. Покупець натискає «Оформити» → «замовлення оформлено» · `submit()@Checkout.ts:40` · зараз: `isDone` 2 → стане: `orderPlaced` 6 · події · Meaning ×3, 2 модулі
2. коли замовлення оформлено, тоді → J1 · `OrderService.create@OrderService.ts:70` · =
3. магазин списує оплату → «оплату проведено» = `paymentCaptured` ⇢ C2 · `OrderService.ts:140` · зараз: HTTP банку в orchestration 0 → стане: `PaymentPort` 6 · виходи · Type ×2, Name
4. замовлення йде на склад · `Warehouse.receive@Warehouse.ts:30` · =

Деталі: `logger.info@Checkout.ts:74` — лог; `retry@Http.ts:30` — retry; `mapToDto@OrderService.ts:95` — мапінг.

Вузли: актор Покупець · дім `Checkout.submit` · подія «замовлення оформлено» · → J1 · зовнішня система банк · HTTP: порту немає, C1a.7 · ⇢ C2

---

Повний збіг з кодом — замість блоку as-is один рядок `to-be = as-is`. Дочірній `Snx` має власний файл і до 3 кроків. Спільний відрізок `Jn` має той самий формат, а в шапці замість точки входу — сценарії, яким служить.
