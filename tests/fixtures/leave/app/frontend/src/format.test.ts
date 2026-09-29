import { describe, expect, it } from 'vitest'
import { formatDate } from './format'

describe('formatDate', () => {
  it('shows an ISO date as day, month and year', () => {
    expect(formatDate('2026-10-05')).toBe('05.10.2026')
  })
})
