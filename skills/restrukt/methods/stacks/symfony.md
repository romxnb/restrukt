# Symfony

Коли: `composer.json` вимагає `symfony/framework-bundle`. Конкретизує тактичний дизайн для Symfony, Doctrine й PHPUnit. Прийнятий у проєкті інший прийом — наприклад, шина команд чи Workflow — важливіший за цей довідник.

| Потреба | Роби | Не роби |
|---|---|---|
| вхід HTTP | дія контролера з атрибутами: `#[MapRequestPayload]` DTO з `#[Assert\…]`, `#[MapQueryParameter]`, `#[MapEntity]`, `#[CurrentUser]`; відповідь `$this->json()`. Коли повідомлення мають іти в заданому порядку, DTO приймає рядки з типовими значеннями, а перевіряє сервіс сценарію | `Request` і розбір тіла вручну; правила й листи в дії; сервіс, що лише повторює дію |
| правило й перехід стану | метод сутності над backed enum; метод, що змінює стан, сам перевіряє попередній | сеттер статусу, рядки статусів у коді |
| порушене правило | один виняток предметної області з `#[WithHttpStatus(422)]` чи `framework.exceptions` | `JsonResponse` з помилкою в кожній гілці; `catch (\Exception)` |
| немає об'єкта, немає права | `createNotFoundException`, `createAccessDeniedException`, `#[IsGranted]`; Voter — коли ту саму перевірку об'єкта кличуть кілька дій | власний виняток на кожен статус |
| вибірка, сума, наявність | названий метод `ServiceEntityRepository` з DQL чи QueryBuilder | інтерфейс репозиторію; фільтр чи сума циклом над сутностями; запит у циклі |
| сценарій із кількома кроками | сервіс, коли кроки мають залежності (пошта, годинник, кілька репозиторіїв) або в сценарію кілька входів; інакше дія контролера | клас на кожен сценарій із методом `execute` або `handle` |
| пошта, час, HTTP, черга | `MailerInterface`, `ClockInterface`, `HttpClientInterface` напряму; Messenger — лише для справжньої асинхронності | власний порт чи обгортка над ними; подія заради одного слухача |
| запис | один `flush()` наприкінці операції; лист після нього | `flush()` посеред правил |
| схема | міграція `doctrine:migrations:diff`, потім `doctrine:schema:validate` | ручна зміна схеми |
| тести | `WebTestCase` через HTTP з тестовою базою; час — `ClockSensitiveTrait::mockTime()`; пошта — `assertEmailCount()`; зовнішній HTTP — `MockHttpClient` | моки власних сервісів і репозиторіїв; тест приватного методу |

Дія з правилом у сутності й винятком, який фреймворк перекладає у 422:

```php
#[Route('/api/invoices/{id}/void', methods: ['POST'])]
public function void(
    #[MapEntity(message: 'Рахунок не знайдено.')] Invoice $invoice,
    EntityManagerInterface $entityManager,
    ClockInterface $clock,
): JsonResponse {
    $this->denyAccessUnlessGranted(InvoiceVoter::MANAGE, $invoice);
    $invoice->void($clock->now()); // кидає InvoiceRuleViolation з #[WithHttpStatus(422)]
    $entityManager->flush();

    return $this->json(['id' => $invoice->getId(), 'status' => $invoice->getStatus()->value]);
}
```

Сервіс виправданий, коли та сама дія має ще вхід із консолі чи черги або кроків більше, ніж дія читає з одного екрана.
