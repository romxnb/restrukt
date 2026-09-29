import { computed, ref } from 'vue'

const STORAGE_KEY = 'employeeId'

function storedEmployeeId(): number | null {
  const stored = localStorage.getItem(STORAGE_KEY)
  return stored === null ? null : Number(stored)
}

export const employeeId = ref<number | null>(storedEmployeeId())
export const isSignedIn = computed(() => employeeId.value !== null)

export function signIn(id: number): void {
  employeeId.value = id
  localStorage.setItem(STORAGE_KEY, String(id))
}

export function signOut(): void {
  employeeId.value = null
  localStorage.removeItem(STORAGE_KEY)
}
