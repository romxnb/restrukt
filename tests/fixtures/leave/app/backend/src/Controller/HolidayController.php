<?php

namespace App\Controller;

use App\Entity\PublicHoliday;
use App\Repository\PublicHolidayRepository;
use Psr\Clock\ClockInterface;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpKernel\Attribute\MapQueryParameter;
use Symfony\Component\Routing\Attribute\Route;

#[Route('/api/holidays')]
final class HolidayController extends AbstractController
{
    private const UPCOMING_LIMIT = 3;

    public function __construct(
        private readonly PublicHolidayRepository $holidays,
        private readonly ClockInterface $clock,
    ) {
    }

    #[Route('', methods: ['GET'])]
    public function list(#[MapQueryParameter] ?int $year = null): JsonResponse
    {
        $year ??= (int) $this->clock->now()->format('Y');
        $holidays = $this->holidays->findBetween(
            new \DateTimeImmutable("$year-01-01"),
            new \DateTimeImmutable("$year-12-31"),
        );

        return $this->json(array_map($this->toJson(...), $holidays));
    }

    #[Route('/upcoming', methods: ['GET'])]
    public function upcoming(): JsonResponse
    {
        $today = $this->clock->now()->setTime(0, 0);

        return $this->json(array_map($this->toJson(...), $this->holidays->findUpcoming($today, self::UPCOMING_LIMIT)));
    }

    /**
     * @return array{date: string, name: string}
     */
    private function toJson(PublicHoliday $holiday): array
    {
        return ['date' => $holiday->getDate()->format('Y-m-d'), 'name' => $holiday->getName()];
    }
}
