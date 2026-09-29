<?php

namespace App\Entity;

use App\Repository\PublicHolidayRepository;
use Doctrine\DBAL\Types\Types;
use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity(repositoryClass: PublicHolidayRepository::class)]
class PublicHoliday
{
    #[ORM\Id]
    #[ORM\GeneratedValue]
    #[ORM\Column]
    private ?int $id = null;

    public function __construct(
        #[ORM\Column(type: Types::DATE_IMMUTABLE, unique: true)]
        private \DateTimeImmutable $date,
        #[ORM\Column(length: 100)]
        private string $name,
    ) {
    }

    public function getId(): ?int
    {
        return $this->id;
    }

    public function getDate(): \DateTimeImmutable
    {
        return $this->date;
    }

    public function getName(): string
    {
        return $this->name;
    }
}
