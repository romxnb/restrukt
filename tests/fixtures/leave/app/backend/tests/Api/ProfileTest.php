<?php

namespace App\Tests\Api;

final class ProfileTest extends ApiTestCase
{
    public function testEmployeeSeesOwnProfileWithTeam(): void
    {
        $team = $this->createTeam('Платформа');
        $olena = $this->createEmployee('Олена Коваль', $team);
        $team->assignManager($olena);
        $this->entityManager->flush();

        $profile = $this->requestAs($olena, 'GET', '/api/me');

        self::assertResponseIsSuccessful();
        self::assertSame('Олена Коваль', $profile['name']);
        self::assertSame('Платформа', $profile['team']['name']);
        self::assertTrue($profile['isManager']);
    }

    public function testRequestWithoutEmployeeIsRejected(): void
    {
        $this->client->request('GET', '/api/me');

        self::assertResponseStatusCodeSame(401);
    }

    public function testEmployeeRenamesThemselves(): void
    {
        $taras = $this->createEmployee('Тарас Мельник', $this->createTeam());

        $profile = $this->requestAs($taras, 'PATCH', '/api/me', ['name' => '  Тарас Мельник-Коваль ']);

        self::assertResponseIsSuccessful();
        self::assertSame('Тарас Мельник-Коваль', $profile['name']);
    }

    public function testBlankNameIsRejectedWithMessage(): void
    {
        $taras = $this->createEmployee('Тарас Мельник', $this->createTeam());

        $error = $this->requestAs($taras, 'PATCH', '/api/me', ['name' => '']);

        self::assertResponseStatusCodeSame(422);
        self::assertSame('Вкажіть ім\'я.', $error['error']);
    }

    public function testTeamMembersAreListedByName(): void
    {
        $team = $this->createTeam();
        $taras = $this->createEmployee('Тарас Мельник', $team);
        $this->createEmployee('Ірина Бондар', $team);
        $this->createEmployee('Марко Шевчук', $this->createTeam('Дизайн'));

        $members = $this->requestAs($taras, 'GET', '/api/team/members');

        self::assertSame(['Ірина Бондар', 'Тарас Мельник'], array_column($members, 'name'));
    }
}
