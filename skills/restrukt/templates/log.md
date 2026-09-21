# Лог restrukt: <проєкт>

## <дата час> · C1a · S1 · зелений зріз

основа: commit збігається; початкові зміни користувача збережені · рецепт: 5 рухів · виконано 5 · пропущено 0 · рядки зрізу 3 · підтверджено поза зрізом 11 · швидкий контракт 104 → 107 · повний suite: очікує завершення C1a · час: кроїльник 4 хв · builder 7 · вердикт 3 · рекомендований коміт: `C1a · S1: orchestration замовлення, порт оплати`

| id | рух | що зроблено | файли |
|---|---|---|---|
| C1a.1 | 1 | `check()` → `reserveStock()` | `OrderService.ts`, `CartView.ts`, `AdminCheckout.ts` |
| C1a.2 | 2 | «замовлення оформлено» = `orderPlaced()` | `Checkout.ts`, `CartView.ts`, `Mail.ts` |
| C1a.7 | 3–5 | `PaymentPort` · `BankHttpAdapter` · з'єднано в `main.ts` | `orders/PaymentPort.ts`, `adapters/BankHttpAdapter.ts`, `main.ts` |

| id | пропущено, бо |
|---|---|
| C1a.4a | рецепт не каже — повернуто в план на декомпозицію |

Імена: `check()` 2 → `reserveStock()` 5 · `PaymentPort` 6 · `OrderService` було 3 «і», стало 2.

Контракт: після скасування резерв знімається, оплата повертається — тримається.

Трасованість: S1 має orchestration home `PlaceOrder.execute()`; `orderPlaced → J1 → payment.capture → paymentCaptured → releaseToWarehouse` читається в причинному порядку; правила резерву й доставки делеговані доменним модулям; банк за `PaymentPort`.

DoD зрізу: 1 виконано · 2 to-be S1 читається з тіла, 4 з 4 кроків · 3 `orderPlaced`, `paymentCaptured` названі · 7 контракт зелений · 8 змін поза рядками немає · 9 імена на обіцяних сходинках · 10 `OrderService` не імпортує `fetch` · решта ще не перевірено.

DoD C1a: очікує 11 підтверджених рядків і повного suite.
