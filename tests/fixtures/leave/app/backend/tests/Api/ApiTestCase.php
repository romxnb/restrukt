<?php

namespace App\Tests\Api;

use App\Entity\Employee;
use App\Entity\PublicHoliday;
use App\Entity\Team;
use Doctrine\ORM\EntityManagerInterface;
use Doctrine\ORM\Tools\SchemaTool;
use Symfony\Bundle\FrameworkBundle\KernelBrowser;
use Symfony\Bundle\FrameworkBundle\Test\WebTestCase;
use Symfony\Component\Clock\Test\ClockSensitiveTrait;

abstract class ApiTestCase extends WebTestCase
{
    use ClockSensitiveTrait;

    protected KernelBrowser $client;
    protected EntityManagerInterface $entityManager;

    protected function setUp(): void
    {
        $this->client = static::createClient();
        $this->entityManager = static::getContainer()->get(EntityManagerInterface::class);

        $metadata = $this->entityManager->getMetadataFactory()->getAllMetadata();
        $schemaTool = new SchemaTool($this->entityManager);
        $schemaTool->dropSchema($metadata);
        $schemaTool->createSchema($metadata);
    }

    protected function createTeam(string $name = 'Платформа'): Team
    {
        $team = new Team($name);
        $this->entityManager->persist($team);
        $this->entityManager->flush();

        return $team;
    }

    protected function createEmployee(string $name, Team $team, int $annualLeaveDays = 24): Employee
    {
        $email = mb_strtolower(str_replace(' ', '.', $name)).'@example.com';
        $employee = new Employee($name, $email, $team, $annualLeaveDays);
        $this->entityManager->persist($employee);
        $this->entityManager->flush();

        return $employee;
    }

    protected function createHoliday(string $date, string $name): PublicHoliday
    {
        $holiday = new PublicHoliday(new \DateTimeImmutable($date), $name);
        $this->entityManager->persist($holiday);
        $this->entityManager->flush();

        return $holiday;
    }

    /**
     * @param array<string, mixed>|null $body
     *
     * @return array<mixed>
     */
    protected function requestAs(Employee $employee, string $method, string $uri, ?array $body = null): array
    {
        $this->client->request(
            $method,
            $uri,
            server: ['HTTP_X_EMPLOYEE_ID' => (string) $employee->getId(), 'CONTENT_TYPE' => 'application/json'],
            content: null === $body ? null : json_encode($body, \JSON_THROW_ON_ERROR),
        );

        return json_decode((string) $this->client->getResponse()->getContent(), true, flags: \JSON_THROW_ON_ERROR);
    }
}
