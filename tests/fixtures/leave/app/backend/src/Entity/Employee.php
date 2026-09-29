<?php

namespace App\Entity;

use App\Repository\EmployeeRepository;
use Doctrine\ORM\Mapping as ORM;
use Symfony\Component\Security\Core\User\UserInterface;

#[ORM\Entity(repositoryClass: EmployeeRepository::class)]
class Employee implements UserInterface
{
    #[ORM\Id]
    #[ORM\GeneratedValue]
    #[ORM\Column]
    private ?int $id = null;

    public function __construct(
        #[ORM\Column(length: 100)]
        private string $name,
        #[ORM\Column(length: 180, unique: true)]
        private string $email,
        #[ORM\ManyToOne]
        #[ORM\JoinColumn(nullable: false)]
        private Team $team,
        #[ORM\Column]
        private int $annualLeaveDays = 24,
    ) {
    }

    public function getId(): ?int
    {
        return $this->id;
    }

    public function getName(): string
    {
        return $this->name;
    }

    public function rename(string $name): void
    {
        $this->name = $name;
    }

    public function getEmail(): string
    {
        return $this->email;
    }

    public function getTeam(): Team
    {
        return $this->team;
    }

    public function getAnnualLeaveDays(): int
    {
        return $this->annualLeaveDays;
    }

    public function isManager(): bool
    {
        return $this->team->getManager() === $this;
    }

    public function getUserIdentifier(): string
    {
        if (null === $this->id) {
            throw new \LogicException('An unsaved employee cannot sign in.');
        }

        return (string) $this->id;
    }

    public function getRoles(): array
    {
        return ['ROLE_EMPLOYEE'];
    }

    public function eraseCredentials(): void
    {
    }
}
