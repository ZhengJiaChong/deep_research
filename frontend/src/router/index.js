import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import ChatResearchView from '../views/ChatResearchView.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView
  },
  {
    path: '/research/:id',
    name: 'research',
    component: ChatResearchView,
    props: true
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
