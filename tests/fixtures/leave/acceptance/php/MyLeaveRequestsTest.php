<?php

namespace App\Tests\Acceptance;

final class MyLeaveRequestsTest extends LeaveAcceptanceTestCase
{
    public function testListShowsOwnRequestsOfYearByStartDateWithBalance(): void
    {
        $later = $this->submitted($this->taras, '2026-04-06', '2026-04-08');
        $earlier = $this->submitted($this->taras, '2026-03-09', '2026-03-13');
        $this->call($this->manager, 'POST', "/api/team/leave-requests/$earlier/approve");
        $this->submitted($this->taras, '2027-02-01', '2027-02-02');
        $this->submitted($this->manager, '2026-05-04', '2026-05-05');

        $mine = $this->call($this->taras, 'GET', '/api/leave-requests');

        self::assertResponseIsSuccessful();
        self::assertSame(2026, $mine['year']);
        self::assertSame([$earlier, $later], array_column($mine['requests'], 'id'));
        self::assertSame(['approved', 'pending'], array_column($mine['requests'], 'status'));
        self::assertSame(['allowance' => 24, 'approved' => 4, 'pending' => 3, 'remaining' => 17], $mine['balance']);
    }

    public function testYearCanBeChosen(): void
    {
        $this->submitted($this->taras, '2026-03-09', '2026-03-13');
        $next = $this->submitted($this->taras, '2027-02-01', '2027-02-02');

        $mine = $this->call($this->taras, 'GET', '/api/leave-requests?year=2027');

        self::assertSame(2027, $mine['year']);
        self::assertSame([$next], array_column($mine['requests'], 'id'));
        self::assertSame(['allowance' => 24, 'approved' => 0, 'pending' => 2, 'remaining' => 22], $mine['balance']);
    }

    public function testCancelledAndRejectedRequestsAreListedButDoNotUseDays(): void
    {
        $cancelled = $this->submitted($this->taras, '2026-03-09', '2026-03-13');
        $this->call($this->taras, 'POST', "/api/leave-requests/$cancelled/cancel");
        $rejected = $this->submitted($this->taras, '2026-03-16', '2026-03-20');
        $this->call($this->manager, 'POST', "/api/team/leave-requests/$rejected/reject", ['reason' => 'Реліз']);

        $mine = $this->call($this->taras, 'GET', '/api/leave-requests');

        self::assertSame(['cancelled', 'rejected'], array_column($mine['requests'], 'status'));
        self::assertSame([null, 'Реліз'], array_column($mine['requests'], 'rejectionReason'));
        self::assertSame(['allowance' => 24, 'approved' => 0, 'pending' => 0, 'remaining' => 24], $mine['balance']);
    }

    public function testOnlyFutureActiveRequestsAreCancellable(): void
    {
        $today = $this->submitted($this->taras, '2026-03-02', '2026-03-03');
        $future = $this->submitted($this->taras, '2026-03-09', '2026-03-10');
        $rejected = $this->submitted($this->taras, '2026-03-16', '2026-03-17');
        $this->call($this->manager, 'POST', "/api/team/leave-requests/$rejected/reject", ['reason' => 'Реліз']);

        $mine = $this->call($this->taras, 'GET', '/api/leave-requests');

        self::assertSame(
            [$today => false, $future => true, $rejected => false],
            array_column($mine['requests'], 'cancellable', 'id'),
        );
    }

    public function testCancellingFutureRequestFreesItsDays(): void
    {
        $id = $this->submitted($this->taras, '2026-03-09', '2026-03-13');

        $cancelled = $this->call($this->taras, 'POST', "/api/leave-requests/$id/cancel");

        self::assertResponseIsSuccessful();
        self::assertSame('cancelled', $cancelled['status']);
        self::assertFalse($cancelled['cancellable']);
        $mine = $this->call($this->taras, 'GET', '/api/leave-requests');
        self::assertSame(24, $mine['balance']['remaining']);
    }

    public function testApprovedFutureRequestCanBeCancelled(): void
    {
        $id = $this->submitted($this->taras, '2026-03-09', '2026-03-13');
        $this->call($this->manager, 'POST', "/api/team/leave-requests/$id/approve");

        $cancelled = $this->call($this->taras, 'POST', "/api/leave-requests/$id/cancel");

        self::assertResponseIsSuccessful();
        self::assertSame('cancelled', $cancelled['status']);
    }

    public function testStartedRequestCannotBeCancelled(): void
    {
        $id = $this->submitted($this->taras, '2026-03-02', '2026-03-06');

        $response = $this->call($this->taras, 'POST', "/api/leave-requests/$id/cancel");

        $this->assertRefused(422, 'Скасувати можна лише заяву, що ще не почалася.', $response);
    }

    public function testCancelledRequestCannotBeCancelledAgain(): void
    {
        $id = $this->submitted($this->taras, '2026-03-09', '2026-03-13');
        $this->call($this->taras, 'POST', "/api/leave-requests/$id/cancel");

        $response = $this->call($this->taras, 'POST', "/api/leave-requests/$id/cancel");

        $this->assertRefused(422, 'Скасувати можна лише заяву, що ще не почалася.', $response);
    }

    public function testColleaguesRequestIsNotFound(): void
    {
        $id = $this->submitted($this->manager, '2026-03-09', '2026-03-13');

        $response = $this->call($this->taras, 'POST', "/api/leave-requests/$id/cancel");

        $this->assertRefused(404, 'Заяву не знайдено.', $response);
    }

    public function testUnknownRequestIsNotFound(): void
    {
        $response = $this->call($this->taras, 'POST', '/api/leave-requests/999/cancel');

        $this->assertRefused(404, 'Заяву не знайдено.', $response);
    }
}
