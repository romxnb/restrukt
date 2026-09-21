# Рецепт зрізу · C1a · S1

основа: commit `<sha>` збігається · рядки зрізу: C1a.1, C1a.2, C1a.7 · швидкий контракт: `npm test -- OrderServiceTests` · повний suite: `npm test` · час кроїльника: N хв

Кожен рух виконується дослівно, по порядку, без рішень. Рух, якого тут немає, не робиться.

| # | id | рух за Фаулером | адреса | що саме | файл призначення | викликачі з ґрепу | тест |
|---|---|---|---|---|---|---|---|
| 1 | C1a.1 | Rename Method | `OrderService.ts:88` `check(items)` | → `reserveStock(items)` | той самий | `OrderService.ts:118`, `CartView.ts:40`, `AdminCheckout.ts:31` | `OrderServiceTests.reserve*` |
| 2 | C1a.2 | Extract Function | `Checkout.ts:40–46` | тіло після `isDone = true` → `orderPlaced(order: Order): void` | `Checkout.ts`, під `submit` | `CartView.ts:40`, `Mail.ts:22` кличуть `orderPlaced` замість читання `isDone` | `OrderServiceTests.placeOrder` |
| 3 | C1a.7 | Extract Interface | `OrderService.ts:140–152` | `interface PaymentPort { capture(order: Order): Promise<PaymentResult> }` | новий `orders/PaymentPort.ts` | — | збірка |
| 4 | C1a.7 | Move Function | `OrderService.ts:140–152` | тіло `fetch(...)` → `class BankHttpAdapter implements PaymentPort` | новий `adapters/BankHttpAdapter.ts` | `OrderService` дістає `payment: PaymentPort` у конструктор | `OrderServiceTests.captures*` з fake `PaymentPort` |
| 5 | C1a.7 | Inline in composition root | `main.ts:12` | `new OrderService(new BankHttpAdapter(config.bankUrl))` | `main.ts` | — | збірка · повний suite при завершенні |

Повернуто в план: C1a.4a — `потребує декомпозиції: інтерфейс StockReservation не має сигнатури в плані`.

Документи: `docs/glossary.md:12` «check» → «reserveStock», рух 1.
