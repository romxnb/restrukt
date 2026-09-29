<?php

namespace App\Command;

use App\Entity\Employee;
use App\Entity\PublicHoliday;
use App\Entity\Team;
use Doctrine\ORM\EntityManagerInterface;
use Symfony\Component\Console\Attribute\AsCommand;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Style\SymfonyStyle;

#[AsCommand(name: 'app:seed-demo', description: 'Fills an empty database with a demo team and holidays')]
final class SeedDemoCommand
{
    private const HOLIDAYS = [
        '01-01' => 'Новий рік',
        '03-08' => 'Міжнародний жіночий день',
        '05-01' => 'День праці',
        '06-28' => 'День Конституції',
        '08-24' => 'День Незалежності',
        '10-01' => 'День захисників і захисниць',
        '12-25' => 'Різдво',
    ];

    public function __construct(private readonly EntityManagerInterface $entityManager)
    {
    }

    public function __invoke(SymfonyStyle $io): int
    {
        $platform = new Team('Платформа');
        $olena = new Employee('Олена Коваль', 'olena@example.com', $platform);
        $taras = new Employee('Тарас Мельник', 'taras@example.com', $platform);
        $iryna = new Employee('Ірина Бондар', 'iryna@example.com', $platform, annualLeaveDays: 28);
        $platform->assignManager($olena);

        $design = new Team('Дизайн');
        $marko = new Employee('Марко Шевчук', 'marko@example.com', $design);
        $design->assignManager($marko);

        foreach ([$platform, $design, $olena, $taras, $iryna, $marko] as $entity) {
            $this->entityManager->persist($entity);
        }

        foreach ([2026, 2027] as $year) {
            foreach (self::HOLIDAYS as $monthDay => $name) {
                $this->entityManager->persist(new PublicHoliday(new \DateTimeImmutable("$year-$monthDay"), $name));
            }
        }

        $this->entityManager->flush();
        $io->success('Demo data created.');

        return Command::SUCCESS;
    }
}
