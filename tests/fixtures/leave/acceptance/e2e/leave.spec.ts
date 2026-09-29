import { expect, test, type APIRequestContext, type Page } from '@playwright/test'

const API = process.env.E2E_API_URL ?? 'http://127.0.0.1:8000'
const HOLIDAYS = ['01-01', '03-08', '05-01', '06-28', '08-24', '10-01', '12-25'] // app:seed-demo

function iso(date: Date): string {
  return date.toISOString().slice(0, 10)
}

function dotted(date: Date): string {
  const [year, month, day] = iso(date).split('-')
  return `${day}.${month}.${year}`
}

/** Monday to Wednesday of a week after `weeksAhead` weeks, in the current year and without holidays. */
function freeWeek(weeksAhead: number): { start: Date; end: Date } | null {
  const today = new Date()
  const start = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate()))
  start.setUTCDate(start.getUTCDate() + 7 * weeksAhead + ((8 - start.getUTCDay()) % 7 || 7))
  for (; start.getUTCFullYear() === today.getUTCFullYear(); start.setUTCDate(start.getUTCDate() + 7)) {
    const end = new Date(start)
    end.setUTCDate(end.getUTCDate() + 2)
    const days = [0, 1, 2].map((offset) => {
      const day = new Date(start)
      day.setUTCDate(day.getUTCDate() + offset)
      return iso(day).slice(5)
    })
    if (end.getUTCFullYear() === start.getUTCFullYear() && !days.some((day) => HOLIDAYS.includes(day))) {
      return { start: new Date(start), end }
    }
  }
  return null
}

async function employeeId(request: APIRequestContext, name: string): Promise<number> {
  const employees: { id: number; name: string }[] = await (await request.get(`${API}/api/employees`)).json()
  const employee = employees.find((candidate) => candidate.name === name)
  if (!employee) throw new Error(`No demo employee ${name}`)
  return employee.id
}

/** The list row (item, table row, card) that shows the period. */
function rowOf(page: Page, start: Date, end: Date) {
  return page
    .locator('li, tr, article, div')
    .filter({ hasText: `${dotted(start)} – ${dotted(end)}` })
    .filter({ hasNot: page.locator('form') })
    .last()
}

async function signInAs(page: Page, name: string) {
  await page.goto('/login')
  await page.getByRole('button', { name: `Увійти як ${name}` }).click()
  await expect(page.getByRole('link', { name: 'Відпустки' })).toBeVisible()
}

test.describe.configure({ mode: 'serial' })

test('employee submits, sees and cancels a leave request', async ({ page }) => {
  const week = freeWeek(1)
  test.skip(week === null, 'no free week left in this year')
  const { start, end } = week!

  await signInAs(page, 'Тарас Мельник')
  await page.getByRole('link', { name: 'Відпустки' }).click()
  await expect(page).toHaveURL(/\/leave$/)
  await expect(page.getByRole('heading', { name: 'Мої відпустки' })).toBeVisible()
  await expect(page.getByText('Річна норма: 24')).toBeVisible()
  await expect(page.getByText('Залишок: 24')).toBeVisible()
  await expect(page.getByText('Заяв цього року немає.')).toBeVisible()
  await expect(page.getByRole('link', { name: 'Заяви команди' })).toHaveCount(0)

  await page.getByLabel('Дата початку').fill(iso(end))
  await page.getByLabel('Дата завершення').fill(iso(start))
  await page.getByRole('button', { name: 'Подати заяву' }).click()
  await expect(page.getByRole('alert')).toHaveText('Дата початку пізніша за дату завершення.')

  await page.getByLabel('Дата початку').fill(iso(start))
  await page.getByLabel('Дата завершення').fill(iso(end))
  await page.getByLabel('Коментар').fill('Море')
  await page.getByRole('button', { name: 'Подати заяву' }).click()

  const row = rowOf(page, start, end)
  await expect(row).toBeVisible()
  await expect(row).toContainText('Робочих днів: 3')
  await expect(row).toContainText('На розгляді')
  await expect(page.getByText('На розгляді: 3')).toBeVisible()
  await expect(page.getByText('Залишок: 21')).toBeVisible()
  await expect(page.getByLabel('Дата початку')).toHaveValue('')
  await expect(page.getByLabel('Коментар')).toHaveValue('')

  await row.getByRole('button', { name: 'Скасувати' }).click()
  await expect(rowOf(page, start, end)).toContainText('Скасовано')
  await expect(page.getByText('Залишок: 24')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Скасувати' })).toHaveCount(0)
})

test('manager approves one request and rejects another with a reason', async ({ page, request }) => {
  const first = freeWeek(2)
  const second = freeWeek(3)
  test.skip(first === null || second === null, 'no free weeks left in this year')
  const iryna = await employeeId(request, 'Ірина Бондар')
  for (const week of [first!, second!]) {
    const response = await request.post(`${API}/api/leave-requests`, {
      headers: { 'X-Employee-Id': String(iryna) },
      data: { startDate: iso(week.start), endDate: iso(week.end) },
    })
    expect(response.status()).toBe(201)
  }

  await signInAs(page, 'Олена Коваль')
  await page.getByRole('link', { name: 'Заяви команди' }).click()
  await expect(page).toHaveURL(/\/team\/leave$/)
  await expect(page.getByRole('heading', { name: 'Заяви команди' })).toBeVisible()
  const firstRow = rowOf(page, first!.start, first!.end)
  const secondRow = rowOf(page, second!.start, second!.end)
  await expect(firstRow).toBeVisible()
  await expect(secondRow).toBeVisible()
  await expect(page.getByText('Ірина Бондар').first()).toBeVisible()

  await page.getByRole('button', { name: 'Погодити' }).first().click()
  await expect(firstRow).toHaveCount(0)

  await page.getByRole('button', { name: 'Відхилити' }).click()
  await page.getByLabel('Причина відмови').fill('Реліз')
  await page.getByRole('button', { name: 'Підтвердити відмову' }).click()
  await expect(page.getByText('Заяв на розгляді немає.')).toBeVisible()

  const mine = await (await request.get(`${API}/api/leave-requests`, { headers: { 'X-Employee-Id': String(iryna) } })).json()
  expect(mine.requests.map((leave: { status: string }) => leave.status)).toEqual(['approved', 'rejected'])

  await signInAs(page, 'Ірина Бондар')
  await page.getByRole('link', { name: 'Відпустки' }).click()
  await expect(rowOf(page, first!.start, first!.end)).toContainText('Погоджено')
  await expect(rowOf(page, second!.start, second!.end)).toContainText('Відхилено')
  await expect(rowOf(page, second!.start, second!.end)).toContainText('Реліз')
  await expect(page.getByText('Погоджено: 3')).toBeVisible()
})
