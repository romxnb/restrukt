<?php

namespace App\Repository;

use App\Entity\Employee;
use App\Entity\Team;
use Doctrine\Bundle\DoctrineBundle\Repository\ServiceEntityRepository;
use Doctrine\Persistence\ManagerRegistry;

/**
 * @extends ServiceEntityRepository<Employee>
 */
class EmployeeRepository extends ServiceEntityRepository
{
    public function __construct(ManagerRegistry $registry)
    {
        parent::__construct($registry, Employee::class);
    }

    /**
     * @return list<Employee>
     */
    public function findAllOrderedByName(): array
    {
        return $this->findBy([], ['name' => 'ASC']);
    }

    /**
     * @return list<Employee>
     */
    public function findTeamMembers(Team $team): array
    {
        return $this->findBy(['team' => $team], ['name' => 'ASC']);
    }
}
