---
description: Ревізія, етап 2 — Маршрут: пройти сценарій від точки входу до термінаторів і заповнити шість реєстрів
argument-hint: "<id або назва сценарію з docs/revision/_map.md>"
---

Виконай етап **Маршрут** процесу Ревізія для сценарію: $1

Спершу прочитай `docs/revision/_map.md`. Якщо файлу немає або робочий набір не обрано — скажи це користувачу і запропонуй `/restrukt:map`. Далі не йди.

Прочитай перед початком:
- `${CLAUDE_PLUGIN_ROOT}/skills/revision/references/vocabulary.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/revision/references/diagrams.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/revision/references/presentation.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/revision/references/stage-walk.md`

Виконай процедуру зі `stage-walk.md` за один прохід: іди від точки входу і заповнюй реєстри по дорозі. Файл — `docs/revision/<сценарій>/<маршрут>.md` за шаблоном `templates/route.md`.

Перед тим як доповісти про завершення, пройди всі одинадцять пунктів воріт виходу вголос, пункт за пунктом.

Якщо шлях `${CLAUDE_PLUGIN_ROOT}` не розкрився у справжню теку — візьми ті самі файли через скіл `revision`.
