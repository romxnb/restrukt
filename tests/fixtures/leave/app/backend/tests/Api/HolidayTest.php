<?php

namespace App\Tests\Api;

final class HolidayTest extends ApiTestCase
{
    public function testHolidaysOfCurrentYearByDefault(): void
    {
        self::mockTime('2026-05-04 09:00');
        $taras = $this->createEmployee('Тарас Мельник', $this->createTeam());
        $this->createHoliday('2025-12-25', 'Різдво');
        $this->createHoliday('2026-08-24', 'День Незалежності');
        $this->createHoliday('2026-01-01', 'Новий рік');

        $holidays = $this->requestAs($taras, 'GET', '/api/holidays');

        self::assertSame(['2026-01-01', '2026-08-24'], array_column($holidays, 'date'));
    }

    public function testUpcomingHolidaysStartToday(): void
    {
        self::mockTime('2026-06-28 18:00');
        $taras = $this->createEmployee('Тарас Мельник', $this->createTeam());
        $this->createHoliday('2026-05-01', 'День праці');
        $this->createHoliday('2026-06-28', 'День Конституції');
        $this->createHoliday('2026-08-24', 'День Незалежності');

        $holidays = $this->requestAs($taras, 'GET', '/api/holidays/upcoming');

        self::assertSame(['День Конституції', 'День Незалежності'], array_column($holidays, 'name'));
    }
}
