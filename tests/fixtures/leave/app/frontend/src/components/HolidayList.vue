<script setup lang="ts">
import type { Holiday } from '@/api/holidays'
import { formatDate } from '@/format'

defineProps<{ holidays: Holiday[] }>()
</script>

<template>
  <p v-if="holidays.length === 0">Найближчих свят немає.</p>
  <ul v-else>
    <li v-for="holiday in holidays" :key="holiday.date">
      <time :datetime="holiday.date">{{ formatDate(holiday.date) }}</time> — {{ holiday.name }}
    </li>
  </ul>
</template>
