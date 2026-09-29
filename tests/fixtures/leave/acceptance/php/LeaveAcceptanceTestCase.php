<?php

namespace App\Tests\Acceptance;

use App\Entity\Employee;
use App\Entity\PublicHoliday;
use App\Entity\Team;
use Doctrine\ORM\EntityManagerInterface;
use Doctrine\ORM\Tools\SchemaTool;
use Symfony\Bundle\FrameworkBundle\KernelBrowser;
use Symfony\Bundle\FrameworkBundle\Test\WebTestCase;
use Symfony\Component\Clock\Test\ClockSensitiveTrait;
use Symfony\Component\Mime\Email;

/**
 * Black-box acceptance of the leave requests spec: only HTTP, e-mails and the pre-existing entities.
 */
abstract class LeaveAcceptanceTestCase extends WebTestCase
{
    use ClockSensitiveTrait;

    protected KernelBrowser $client;
    protected EntityManagerInterface $entityManager;
    protected Team $team;
    protected Employee $manager;
    protected Employee $taras;

    protected function setUp(): void
    {
        self::mockTime('2026-03-02 10:00'); // Monday
        $this->client = static::createClient();
        $this->entityManager = static::getContainer()->get(EntityManagerInterface::class);
        $metadata = $this->entityManager->getMetadataFactory()->getAllMetadata();
        $schemaTool = new SchemaTool($this->entityManager);
        $schemaTool->dropSchema($metadata);
        $schemaTool->createSchema($metadata);

        $this->team = new Team('Платформа');
        $this->entityManager->persist($this->team);
        $this->manager = $this->employee('Олена Коваль', $this->team);
        $this->taras = $this->employee('Тарас Мельник', $this->team);
        $this->team->assignManager($this->manager);
        $this->holiday('2026-03-11', 'Тестове свято'); // Wednesday
        $this->entityManager->flush();
    }

    protected function employee(string $name, Team $team, int $annualLeaveDays = 24): Employee
    {
        static $number = 0;
        ++$number;
        $employee = new Employee($name, "employee$number@example.com", $team, $annualLeaveDays);
        $this->entityManager->persist($employee);
        $this->entityManager->flush();

        return $employee;
    }

    protected function holiday(string $date, string $name): void
    {
        $this->entityManager->persist(new PublicHoliday(new \DateTimeImmutable($date), $name));
        $this->entityManager->flush();
    }

    /**
     * @return array<mixed>
     */
    protected function call(Employee $employee, string $method, string $uri, ?array $body = null): array
    {
        $this->client->request(
            $method,
            $uri,
            server: ['HTTP_X_EMPLOYEE_ID' => (string) $employee->getId(), 'CONTENT_TYPE' => 'application/json', 'HTTP_ACCEPT' => 'application/json'],
            content: null === $body ? null : json_encode($body, \JSON_THROW_ON_ERROR),
        );
        $content = (string) $this->client->getResponse()->getContent();

        return '' === $content ? [] : (array) json_decode($content, true, flags: \JSON_THROW_ON_ERROR);
    }

    protected function submit(Employee $employee, string $start, string $end, ?string $comment = null): array
    {
        $body = ['startDate' => $start, 'endDate' => $end];
        if (null !== $comment) {
            $body['comment'] = $comment;
        }

        return $this->call($employee, 'POST', '/api/leave-requests', $body);
    }

    protected function submitted(Employee $employee, string $start, string $end): int
    {
        $request = $this->submit($employee, $start, $end);
        self::assertResponseStatusCodeSame(201, json_encode($request, \JSON_UNESCAPED_UNICODE));

        return $request['id'];
    }

    protected function assertRefused(int $status, string $message, array $response): void
    {
        self::assertResponseStatusCodeSame($status, json_encode($response, \JSON_UNESCAPED_UNICODE));
        self::assertSame($message, $response['error'] ?? null);
    }

    /**
     * @return list<Email>
     */
    protected function sentEmails(): array
    {
        /** @var list<Email> */
        return array_values(array_filter(self::getMailerMessages(), static fn ($message) => $message instanceof Email));
    }
}
