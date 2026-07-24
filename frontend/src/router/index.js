import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import FinanceView from '@/views/FinanceView.vue'
import StrategyView from '@/views/StrategyView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/analysis/:filename',
      name: 'analysis',
      component: FinanceView,
    },
    {
      path: '/strategy/:filename',
      name: 'strategy',
      component: StrategyView,
    },
    {
      path: '/about',
      name: 'about',
      component: () => import('../views/AboutView.vue'),
    },
  ],
})

export default router
