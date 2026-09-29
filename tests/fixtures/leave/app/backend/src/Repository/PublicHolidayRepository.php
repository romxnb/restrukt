<?php

namespace App\Repository;

use App\Entity\PublicHoliday;
use Doctrine\Bundle\DoctrineBundle\Repository\ServiceEntityRepository;
use Doctrine\Persistence\ManagerRegistry;

/**
 * @extends ServiceEntityRepository<PublicHoliday>
 */
class PublicHolidayRepository extends ServiceEntityRepository
{
    public function __construct(ManagerRegistry $registry)
    {
        parent::__construct($registry, PublicHoliday::class);
    }

    /**
     * @return list<PublicHoliday>
     */
    public function findBetween(\DateTimeImmutable $from, \DateTimeImmutable $to): array
    {
        return $this->createQueryBuilder('holiday')
            ->where('holiday.date BETWEEN :from AND :to')
            ->setParameter('from', $from->format('Y-m-d'))
            ->setParameter('to', $to->format('Y-m-d'))
            ->orderBy('holiday.date', 'ASC')
            ->getQuery()
            ->getResult();
    }

    /**
     * @return list<PublicHoliday>
     */
    public function findUpcoming(\DateTimeImmutable $today, int $limit): array
    {
        return $this->createQueryBuilder('holiday')
            ->where('holiday.date >= :today')
            ->setParameter('today', $today->format('Y-m-d'))
            ->orderBy('holiday.date', 'ASC')
            ->setMaxResults($limit)
            ->getQuery()
            ->getResult();
    }
}
