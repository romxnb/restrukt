<?php

namespace App\Tests\Acceptance;

use App\Entity\Team;

final class TeamLeaveRequestsTest extends LeaveAcceptanceTestCase
{
    public function testManagerSeesPendingRequestsOfTeamByStartDate(): void
    {
        $iryna = $this->employee('Ірина Бондар', $this->team);
        $design = new Team('Дизайн');
        $this->entityManager->persist($design);
        $marko = $this->employee('Марко Шевчук', $design);
        $later = $this->submitted($this->taras, '2026-04-06', '2026-04-08');
        $earlier = $this->submitted($iryna, '2026-03-09', '2026-03-10');
        $approved = $this->submitted($iryna, '2026-05-04', '2026-05-05');
        $this->call($this->manager, 'POST', "/api/team/leave-requests/$approved/approve");
        $this->submitted($marko, '2026-03-09', '2026-03-10');
        $this->submitted($this->manager, '2026-06-01', '2026-06-02');

        $pending = $this->call($this->manager, 'GET', '/api/team/leave-requests');

        self::assertResponseIsSuccessful();
        self::assertSame([$earlier, $later], array_column($pending, 'id'));
        self::assertSame(['id' => $iryna->getId(), 'name' => 'Ірина Бондар'], $pending[0]['employee']);
        self::assertSame('2026-03-09', $pending[0]['startDate']);
        self::assertSame('2026-03-10', $pending[0]['endDate']);
        self::assertSame(2, $pending[0]['workingDays']);
        self::assertArrayHasKey('comment', $pending[0]);
    }

    public function testEmployeeWhoIsNotManagerCannotSeeTeamRequests(): void
    {
        $response = $this->call($this->taras, 'GET', '/api/team/leave-requests');

        $this->assertRefused(403, 'Доступно лише керівнику команди.', $response);
    }

    public function testManagerApprovesRequestAndEmployeeIsNotified(): void
    {
        $id = $this->submitted($this->taras, '2026-03-09', '2026-03-13');

        $decision = $this->call($this->manager, 'POST', "/api/team/leave-requests/$id/approve");

        self::assertResponseIsSuccessful();
        self::assertSame(['id' => $id, 'status' => 'approved', 'rejectionReason' => null], $decision);
        $emails = $this->sentEmails();
        self::assertCount(1, $emails);
        self::assertSame($this->taras->getEmail(), $emails[0]->getTo()[0]->getAddress());
        self::assertSame('Заяву погоджено', $emails[0]->getSubject());
        $mine = $this->call($this->taras, 'GET', '/api/leave-requests');
        self::assertSame(['allowance' => 24, 'approved' => 4, 'pending' => 0, 'remaining' => 20], $mine['balance']);
    }

    public function testManagerRejectsRequestWithReason(): void
    {
        $id = $this->submitted($this->taras, '2026-03-09', '2026-03-13');

        $decision = $this->call($this->manager, 'POST', "/api/team/leave-requests/$id/reject", ['reason' => 'Реліз']);

        self::assertResponseIsSuccessful();
        self::assertSame(['id' => $id, 'status' => 'rejected', 'rejectionReason' => 'Реліз'], $decision);
        $emails = $this->sentEmails();
        self::assertCount(1, $emails);
        self::assertSame('Заяву відхилено', $emails[0]->getSubject());
        $text = (string) ($emails[0]->getTextBody() ?? strip_tags((string) $emails[0]->getHtmlBody()));
        self::assertStringContainsString('Реліз', $text);
    }

    public function testRejectionNeedsReason(): void
    {
        $id = $this->submitted($this->taras, '2026-03-09', '2026-03-13');

        $withoutReason = $this->call($this->manager, 'POST', "/api/team/leave-requests/$id/reject", []);
        $this->assertRefused(422, 'Вкажіть причину відмови.', $withoutReason);
        $emptyReason = $this->call($this->manager, 'POST', "/api/team/leave-requests/$id/reject", ['reason' => '']);
        $this->assertRefused(422, 'Вкажіть причину відмови.', $emptyReason);
    }

    public function testDecidedRequestCannotBeDecidedAgain(): void
    {
        $id = $this->submitted($this->taras, '2026-03-09', '2026-03-13');
        $this->call($this->manager, 'POST', "/api/team/leave-requests/$id/approve");

        $approveAgain = $this->call($this->manager, 'POST', "/api/team/leave-requests/$id/approve");
        $this->assertRefused(422, 'Заяву вже розглянуто.', $approveAgain);
        $rejectAfter = $this->call($this->manager, 'POST', "/api/team/leave-requests/$id/reject", ['reason' => 'Реліз']);
        $this->assertRefused(422, 'Заяву вже розглянуто.', $rejectAfter);
    }

    public function testCancelledRequestCannotBeApproved(): void
    {
        $id = $this->submitted($this->taras, '2026-03-09', '2026-03-13');
        $this->call($this->taras, 'POST', "/api/leave-requests/$id/cancel");

        $response = $this->call($this->manager, 'POST', "/api/team/leave-requests/$id/approve");

        $this->assertRefused(422, 'Заяву вже розглянуто.', $response);
    }

    public function testManagerOfAnotherTeamCannotDecide(): void
    {
        $design = new Team('Дизайн');
        $this->entityManager->persist($design);
        $marko = $this->employee('Марко Шевчук', $design);
        $design->assignManager($marko);
        $this->entityManager->flush();
        $id = $this->submitted($this->taras, '2026-03-09', '2026-03-13');

        $response = $this->call($marko, 'POST', "/api/team/leave-requests/$id/approve");

        $this->assertRefused(403, 'Доступно лише керівнику команди.', $response);
    }

    public function testEmployeeCannotApproveColleaguesRequest(): void
    {
        $iryna = $this->employee('Ірина Бондар', $this->team);
        $id = $this->submitted($iryna, '2026-03-09', '2026-03-13');

        $response = $this->call($this->taras, 'POST', "/api/team/leave-requests/$id/approve");

        $this->assertRefused(403, 'Доступно лише керівнику команди.', $response);
    }

    public function testUnknownRequestIsNotFoundForManager(): void
    {
        $response = $this->call($this->manager, 'POST', '/api/team/leave-requests/999/approve');

        $this->assertRefused(404, 'Заяву не знайдено.', $response);
    }
}
