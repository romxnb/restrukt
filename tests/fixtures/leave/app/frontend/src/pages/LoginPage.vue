<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { fetchEmployees, type EmployeeSummary } from '@/api/employees'
import { signIn } from '@/session'

const router = useRouter()
const employees = ref<EmployeeSummary[]>([])
const error = ref('')

onMounted(async () => {
  try {
    employees.value = await fetchEmployees()
  } catch (e) {
    error.value = (e as Error).message
  }
})

function enterAs(employee: EmployeeSummary) {
  signIn(employee.id)
  router.push('/')
}
</script>

<template>
  <h1>Демо-вхід</h1>
  <p v-if="error" class="error">{{ error }}</p>
  <ul>
    <li v-for="employee in employees" :key="employee.id">
      <button type="button" @click="enterAs(employee)">Увійти як {{ employee.name }}</button>
    </li>
  </ul>
</template>
