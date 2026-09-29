<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { fetchProfile, updateProfile, type Profile } from '@/api/employees'
import { fetchUpcomingHolidays, type Holiday } from '@/api/holidays'
import HolidayList from '@/components/HolidayList.vue'

const profile = ref<Profile | null>(null)
const holidays = ref<Holiday[]>([])
const newName = ref('')
const saving = ref(false)
const error = ref('')

onMounted(async () => {
  try {
    ;[profile.value, holidays.value] = await Promise.all([fetchProfile(), fetchUpcomingHolidays()])
    newName.value = profile.value.name
  } catch (e) {
    error.value = (e as Error).message
  }
})

async function rename() {
  saving.value = true
  error.value = ''
  try {
    profile.value = await updateProfile(newName.value)
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <p v-if="error" class="error" role="alert">{{ error }}</p>
  <template v-if="profile">
    <h1>Вітаємо, {{ profile.name }}</h1>
    <p>Команда: {{ profile.team.name }}</p>

    <form @submit.prevent="rename">
      <label>
        Ім'я
        <input v-model="newName" name="name" required />
      </label>
      <button type="submit" :disabled="saving">Зберегти</button>
    </form>
  </template>

  <h2>Найближчі свята</h2>
  <HolidayList :holidays="holidays" />
</template>
