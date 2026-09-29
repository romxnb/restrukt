import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '@/api/client'
import * as employees from '@/api/employees'
import * as holidays from '@/api/holidays'
import HomePage from './HomePage.vue'

const olena: employees.Profile = {
  id: 1,
  name: 'Олена Коваль',
  email: 'olena@example.com',
  team: { id: 1, name: 'Платформа' },
  isManager: true,
}

describe('HomePage', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    vi.spyOn(employees, 'fetchProfile').mockResolvedValue(olena)
    vi.spyOn(holidays, 'fetchUpcomingHolidays').mockResolvedValue([])
  })

  it('greets the employee and names the team', async () => {
    const page = mount(HomePage)
    await flushPromises()

    expect(page.get('h1').text()).toBe('Вітаємо, Олена Коваль')
    expect(page.text()).toContain('Команда: Платформа')
  })

  it('shows why a new name was rejected', async () => {
    vi.spyOn(employees, 'updateProfile').mockRejectedValue(new ApiError("Вкажіть ім'я.", 422))
    const page = mount(HomePage)
    await flushPromises()

    await page.get('form').trigger('submit')
    await flushPromises()

    expect(page.get('[role="alert"]').text()).toBe("Вкажіть ім'я.")
  })
})
