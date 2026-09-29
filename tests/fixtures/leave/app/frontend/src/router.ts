import { createRouter, createWebHistory } from 'vue-router'
import { isSignedIn } from './session'
import HomePage from './pages/HomePage.vue'
import LoginPage from './pages/LoginPage.vue'
import TeamPage from './pages/TeamPage.vue'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: LoginPage, meta: { public: true } },
    { path: '/', component: HomePage },
    { path: '/team', component: TeamPage },
  ],
})

router.beforeEach((to) => {
  if (!to.meta.public && !isSignedIn.value) {
    return '/login'
  }
})
