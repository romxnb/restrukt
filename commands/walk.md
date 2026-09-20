---
description: Ревізія — ще один маршрут: інвентар і шари 1–2 судження для названого сценарію
argument-hint: "<id або назва сценарію з docs/revision/_map.md>"
---

Пройди маршрут для сценарію: $1

Прочитай `docs/revision/_map.md`. Немає — запропонуй `/restrukt:run`. Далі не йди.

Прочитай `${CLAUDE_PLUGIN_ROOT}/skills/revision/references/orchestration.md`.

`date '+%H:%M:%S'`. Обери маршрут за правилом `orchestration.md`, запусти **одного** `revision-walker` з наступним вільним id `wN` і переліком джерел мови з `_map.md`. Злий уламок журналу, створи запропоновані фрагменти, познач маршрут пройденим у `_map.md`.

Покажи таблиці шарів 1 і 2, як у `/restrukt:run`, і зупинись перед правками.

Якщо `${CLAUDE_PLUGIN_ROOT}` не розкрився — ті самі файли через скіл `revision`.
