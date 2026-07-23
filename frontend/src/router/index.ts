import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard/index.vue')
  },
  {
    path: '/market',
    name: 'Market',
    component: () => import('@/views/Market/index.vue')
  },
  {
    path: '/stock/:code?',
    name: 'Stock',
    component: () => import('@/views/Stock/detail.vue')
  },
  {
    path: '/indicator',
    name: 'Indicator',
    component: () => import('@/views/Indicator/index.vue')
  },
  {
    path: '/capital',
    name: 'Capital',
    component: () => import('@/views/Capital/index.vue')
  },
  {
    path: '/watchlist',
    name: 'WatchList',
    component: () => import('@/views/WatchList/index.vue')
  },
  {
    path: '/datacenter',
    name: 'DataCenter',
    component: () => import('@/views/DataCenter/index.vue')
  },
  {
    path: '/ai',
    name: 'AI',
    component: () => import('@/views/AI/index.vue')
  },
  {
    path: '/knowledge',
    name: 'Knowledge',
    component: () => import('@/views/KnowledgeBase/index.vue')
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings/index.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
