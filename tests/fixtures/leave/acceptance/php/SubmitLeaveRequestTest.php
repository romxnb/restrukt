<?php

namespace App\Tests\Acceptance;

final class SubmitLeaveRequestTest extends LeaveAcceptanceTestCase
{
    public function testRequestCountsWorkingDaysWithoutWeekendsAndHolidays(): void
    {
        $request = $this->submit($this->taras, '2026-03-09', '2026-03-15', 'Море');

        self::assertResponseStatusCodeSame(201);
        self::assertSame('2026-03-09', $request['startDate']);
        self::assertSame('2026-03-15', $request['endDate']);
        self::assertSame(4, $request['workingDays']);
        self::assertSame('pending', $request['status']);
        self::assertSame('Море', $request['comment']);
        self::assertNull($request['rejectionReason']);
        self::assertTrue($request['cancellable']);
        self::assertIsInt($request['id']);
    }

    public function testRequestMayStartToday(): void
    {
        $this->submit($this->taras, '2026-03-02', '2026-03-02');

        self::assertResponseStatusCodeSame(201);
    }

    public function testCommentIsOptional(): void
    {
        $request = $this->submit($this->taras, '2026-03-02', '2026-03-03');

        self::assertResponseStatusCodeSame(201);
        self::assertNull($request['comment']);
    }

    public function testManagerIsNotifiedAboutNewRequest(): void
    {
        $this->submit($this->taras, '2026-03-09', '2026-03-13');

        $emails = $this->sentEmails();
        self::assertCount(1, $emails);
        self::assertSame($this->manager->getEmail(), $emails[0]->getTo()[0]->getAddress());
        self::assertSame('Нова заява на відпустку', $emails[0]->getSubject());
        $text = (string) ($emails[0]->getTextBody() ?? strip_tags((string) $emails[0]->getHtmlBody()));
        self::assertStringContainsString('Тарас Мельник', $text);
        self::assertStringContainsString('4', $text);
    }

    public function testManagersOwnRequestIsApprovedAtOnceWithoutEmail(): void
    {
        $request = $this->submit($this->manager, '2026-03-09', '2026-03-13');

        self::assertResponseStatusCodeSame(201);
        self::assertSame('approved', $request['status']);
        self::assertCount(0, $this->sentEmails());
    }

    /**
     * @return iterable<string, array{array<string, mixed>, string}>
     */
    public static function refusals(): iterable
    {
        yield 'date in another format' => [['startDate' => '09.03.2026', 'endDate' => '2026-03-13'], 'Вкажіть дати у форматі РРРР-ММ-ДД.'];
        yield 'missing end date' => [['startDate' => '2026-03-09'], 'Вкажіть дати у форматі РРРР-ММ-ДД.'];
        yield 'impossible date' => [['startDate' => '2026-02-30', 'endDate' => '2026-03-13'], 'Вкажіть дати у форматі РРРР-ММ-ДД.'];
        yield 'start after end' => [['startDate' => '2026-03-13', 'endDate' => '2026-03-09'], 'Дата початку пізніша за дату завершення.'];
        yield 'start after end in the past' => [['startDate' => '2026-02-10', 'endDate' => '2026-02-02'], 'Дата початку пізніша за дату завершення.'];
        yield 'start in the past' => [['startDate' => '2026-02-27', 'endDate' => '2026-03-03'], 'Не можна подати заяву на минулу дату.'];
        yield 'two years' => [['startDate' => '2026-12-28', 'endDate' => '2027-01-05'], 'Заява не може охоплювати два роки.'];
        yield 'weekend only' => [['startDate' => '2026-03-14', 'endDate' => '2026-03-15'], 'У вибраному періоді немає робочих днів.'];
        yield 'holiday only' => [['startDate' => '2026-03-11', 'endDate' => '2026-03-11'], 'У вибраному періоді немає робочих днів.'];
        yield 'long comment' => [['startDate' => '2026-03-09', 'endDate' => '2026-03-13', 'comment' => str_repeat('я', 501)], 'Коментар не довший за 500 символів.'];
    }

    #[\PHPUnit\Framework\Attributes\DataProvider('refusals')]
    public function testInvalidRequestIsRefusedWithReason(array $body, string $message): void
    {
        $response = $this->call($this->taras, 'POST', '/api/leave-requests', $body);

        $this->assertRefused(422, $message, $response);
    }

    public function testCommentOfFiveHundredCharactersIsAccepted(): void
    {
        $this->submit($this->taras, '2026-03-09', '2026-03-13', str_repeat('я', 500));

        self::assertResponseStatusCodeSame(201);
    }

    public function testRequestOverlappingPendingOneIsRefused(): void
    {
        $this->submitted($this->taras, '2026-03-09', '2026-03-13');

        $response = $this->submit($this->taras, '2026-03-13', '2026-03-17');

        $this->assertRefused(422, 'Період перетинається з іншою заявою.', $response);
    }

    public function testRequestOverlappingCancelledOrRejectedOneIsAccepted(): void
    {
        $cancelled = $this->submitted($this->taras, '2026-03-09', '2026-03-13');
        $this->call($this->taras, 'POST', "/api/leave-requests/$cancelled/cancel");
        $rejected = $this->submitted($this->taras, '2026-03-16', '2026-03-20');
        $this->call($this->manager, 'POST', "/api/team/leave-requests/$rejected/reject", ['reason' => 'Реліз']);

        $this->submit($this->taras, '2026-03-12', '2026-03-17');

        self::assertResponseStatusCodeSame(201);
    }

    public function testRequestsOfColleaguesDoNotOverlap(): void
    {
        $this->submitted($this->manager, '2026-03-09', '2026-03-13');

        $this->submit($this->taras, '2026-03-09', '2026-03-13');

        self::assertResponseStatusCodeSame(201);
    }

    public function testRequestLongerThanRemainingDaysIsRefused(): void
    {
        $iryna = $this->employee('Ірина Бондар', $this->team, annualLeaveDays: 5);
        $this->submitted($iryna, '2026-03-02', '2026-03-04');

        $response = $this->submit($iryna, '2026-03-16', '2026-03-18');

        $this->assertRefused(422, 'Недостатньо днів відпустки: залишилось 2.', $response);
    }

    public function testRequestUsingExactlyRemainingDaysIsAccepted(): void
    {
        $iryna = $this->employee('Ірина Бондар', $this->team, annualLeaveDays: 5);
        $this->submitted($iryna, '2026-03-02', '2026-03-04');

        $this->submit($iryna, '2026-03-16', '2026-03-17');

        self::assertResponseStatusCodeSame(201);
    }

    public function testOverlapIsReportedBeforeInsufficientDays(): void
    {
        $iryna = $this->employee('Ірина Бондар', $this->team, annualLeaveDays: 5);
        $this->submitted($iryna, '2026-03-02', '2026-03-06');

        $response = $this->submit($iryna, '2026-03-06', '2026-03-10');

        $this->assertRefused(422, 'Період перетинається з іншою заявою.', $response);
    }

    public function testAllowanceOfNextYearIsSeparate(): void
    {
        $iryna = $this->employee('Ірина Бондар', $this->team, annualLeaveDays: 5);
        $this->submitted($iryna, '2026-03-02', '2026-03-06');

        $this->submit($iryna, '2027-01-11', '2027-01-15');

        self::assertResponseStatusCodeSame(201);
    }

    public function testUnknownEmployeeIsNotAuthenticated(): void
    {
        $this->client->request('GET', '/api/leave-requests');

        self::assertResponseStatusCodeSame(401);
    }
}
