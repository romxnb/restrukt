# Діаграми

Діаграма ставиться там, де спрацювала умова.

| Діаграма | Тип mermaid | Обов'язкова, коли | Файл |
|---|---|---|---|
| Маршрут | `sequenceDiagram` | завжди, у шапці | маршрут |
| Стан | `flowchart LR` | сутність має чужих писарів | маршрут |
| Життєвий цикл | `stateDiagram-v2` | маршрут міняє статус сутності | маршрут |
| Карта сценаріїв | `flowchart LR` | повний огляд | `_map.md` |
| Цільова карта | `flowchart LR` | шар 5 | судження |
| Кластер | `flowchart LR` | завжди | фрагмент |

Понад 12 вузлів — клубок. Розбивай або згортай.

## Ідентифікатори

Префікс латиницею, підпис українською, ідентифікатор першим у підписі. Вузол діаграми дорівнює рядку таблиці.

`IN` вхід · `ST` крок · `DE` рішення · `EF` ефект · `FA` факт · `BO` межа · `SK` непройдені двері · `S` сутність стану · `OW` чужий писар · `MO` модуль цільової карти · `J` рядок судження

Колір і форма позначають клас, не якість: червоних вузлів для «поганого» в інвентарі немає.

## Зразки

```mermaid
sequenceDiagram
  participant U as Користувач
  participant A as API
  participant D as Сховище
  U->>A: ST2 POST /orders/:id/pay
  A->>D: ST6 запис статусу
```

```mermaid
flowchart LR
  ST3[ST3] -->|читає| S1[(orders.status)]
  ST6[ST6] -->|пише| S1
  OW1[OW1 refund.ts:31] -->|пише| S1
```

```mermaid
flowchart LR
  MO1[MO1 SessionController]:::keep
  MO2[MO2 SessionPlan]:::new
  MO4[MO4 AppModel]:::gone
  MO4 --> MO1 --> MO2
  classDef keep stroke-width:1px
  classDef new stroke-width:3px
  classDef gone stroke-dasharray:4
```

Товста рамка — модуль, якого ще немає. Пунктир — модуль, який зникає.
