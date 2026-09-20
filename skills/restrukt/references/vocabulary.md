# Словник

Методи не переказуються: називається ім'я, агент знає його за ключовим словом. Тут лише терміни цього плагіна і перелік імен, які він цитує.

## Процес

За таксономією Chikofsky & Cross, 1990:

| Етап | Їхній термін | Правило, що з нього випливає |
|---|---|---|
| 1 Збір | reverse engineering, design recovery | систему не змінює; піднімає висоту подання, а не переписує код іншою формою (redocumentation) |
| 2 Узгодження | — | Chat with the Maintainers, OORP |
| 3 Виконання | restructuring | поведінка та сама, форма інша |
| restrukt цілком | reengineering | |

## Терміни плагіна

| Термін | Означення |
|---|---|
| **точка входу** | місце, звідки виконання починається ззовні; знаходиться ґрепом |
| **сценарій** | Use Case рівня моря за Кокберном: актор + дієслово + результат |
| **маршрут** | файли і функції, якими сценарій іде від точки входу до кінця |
| **кластер** | маршрути зі спільними файлами або станом; одиниця узгодження і виконання, пачка |
| **кошик** | одна з шести груп пропозицій: слова, події, правила, межі, склад, місце; порядок кошиків є порядком виконання |
| **пропозиція** | рядок плану: де, зараз, пропоную, чому, стан |
| **чому** | міра за connascence, Пейдж-Джонс: форма, ступінь, відстань, плюс рядки |
| **шлях** | набір рядків на один прогін виконання; Most Valuable First |
| **контракт** | що має лишитись правдою: наявні тести кластера і до п'яти поведінок; Characterization Test за Фезерсом |
| **джерело мови** | документ проєкту з термінами: файл контексту агента, README, `docs/`, ADR; Ubiquitous Language за Евансом, не наказ |
| **розходження** | пропоноване ім'я відрізняється від документного; показується з підставою, вирішує користувач, підтверджене править і документ |
| **сходинка** | зрілість імені 0–6, Naming as a Process за Белші |

## Імена, які плагін цитує

OORP, Демейер, Дюкасс, Нірштрас: Skim the Documentation · Read All the Code in One Hour · Study the Exceptional Entities · Analyze the Persistent Data · Speculate about Design · Tie Code and Questions · Chat with the Maintainers · Agree on Maxims · Most Valuable First · Fix Problems Not Symptoms · If It Ain't Broke Don't Fix It · Write Tests to Enable Evolution · Record Business Rules as Tests · Regression Test After Every Change · Always Have a Running Version · Migrate Systems Incrementally · Conserve Familiarity · Redistribute Responsibilities · Move Behavior Close to Data · Split Up God Class · Transform Conditionals to Polymorphism · Factor out Strategy · Detecting Duplicated Code.

Connascence, Пейдж-Джонс і Вайріх: Name · Type · Meaning · Position · Algorithm · Execution · Timing · Value · Identity; сила, ступінь, відстань.

Лінзи кошиків: Linguistic Antipatterns, Арнаудова · Naming as a Process і Honest and Complete Name, Белші · Ubiquitous Language, Domain Event, Aggregate, Еванс · Policy, Брандоліні · Fail-safe defaults, Зальцер і Шредер · Module, Парнас · Screaming Architecture, Мартін · Divergent Change, каталог рефакторингів, Фаулер · Strangler Fig.

## Види точок входу

HTTP-роут · GraphQL-резолвер · RPC-метод · CLI-команда · обробник події інтерфейсу · консюмер черги · підписник на подію · запланована задача · вебхук · публічний експорт · хук старту або міграції.
