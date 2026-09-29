<script setup lang="ts">
import { useRouter } from 'vue-router'
import { isSignedIn, signOut } from './session'

const router = useRouter()

function leave() {
  signOut()
  router.push('/login')
}
</script>

<template>
  <header v-if="isSignedIn" class="navigation">
    <nav>
      <RouterLink to="/">Головна</RouterLink>
      <RouterLink to="/team">Команда</RouterLink>
    </nav>
    <button type="button" @click="leave">Вийти</button>
  </header>
  <main>
    <RouterView />
  </main>
</template>

<style scoped>
.navigation {
  display: flex;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #e4e7eb;
}

nav {
  display: flex;
  gap: 1rem;
}
</style>
