import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import HolidayList from './HolidayList.vue'

describe('HolidayList', () => {
  it('lists holidays with formatted dates', () => {
    const list = mount(HolidayList, { props: { holidays: [{ date: '2026-08-24', name: 'День Незалежності' }] } })

    expect(list.text()).toContain('24.08.2026 — День Незалежності')
  })

  it('says when there are no holidays', () => {
    const list = mount(HolidayList, { props: { holidays: [] } })

    expect(list.text()).toBe('Найближчих свят немає.')
  })
})
