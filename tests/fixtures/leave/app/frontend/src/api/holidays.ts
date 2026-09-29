import { api } from './client'

export interface Holiday {
  date: string
  name: string
}

export const fetchUpcomingHolidays = () => api.get<Holiday[]>('/api/holidays/upcoming')
