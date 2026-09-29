import { api } from './client'

export interface EmployeeSummary {
  id: number
  name: string
}

export interface Profile {
  id: number
  name: string
  email: string
  team: { id: number; name: string }
  isManager: boolean
}

export interface TeamMember {
  id: number
  name: string
  email: string
  isManager: boolean
}

export const fetchEmployees = () => api.get<EmployeeSummary[]>('/api/employees')
export const fetchProfile = () => api.get<Profile>('/api/me')
export const updateProfile = (name: string) => api.patch<Profile>('/api/me', { name })
export const fetchTeamMembers = () => api.get<TeamMember[]>('/api/team/members')
