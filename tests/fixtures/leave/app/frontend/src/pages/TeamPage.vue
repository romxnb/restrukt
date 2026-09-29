<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { fetchTeamMembers, type TeamMember } from '@/api/employees'

const members = ref<TeamMember[]>([])
const error = ref('')

onMounted(async () => {
  try {
    members.value = await fetchTeamMembers()
  } catch (e) {
    error.value = (e as Error).message
  }
})
</script>

<template>
  <h1>Команда</h1>
  <p v-if="error" class="error" role="alert">{{ error }}</p>
  <table v-else>
    <thead>
      <tr>
        <th>Ім'я</th>
        <th>Пошта</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="member in members" :key="member.id">
        <td>
          {{ member.name }}
          <span v-if="member.isManager">(керівник)</span>
        </td>
        <td>{{ member.email }}</td>
      </tr>
    </tbody>
  </table>
</template>
