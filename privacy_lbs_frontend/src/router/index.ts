import { createRouter, createWebHistory } from 'vue-router'
import AppLayout from '@/layouts/AppLayout.vue'
import HomeView from '@/views/HomeView.vue'
import DemoView from '@/views/DemoView.vue'
import DashboardView from '@/views/DashboardView.vue'
import ResultsAnalysisView from '@/views/ResultsAnalysisView.vue'
import ConfigView from '@/views/ConfigView.vue'
import TestMapView from '@/views/TestMapView.vue'
import DataManagementView from '@/views/DataManagementView.vue'
import QueryHistoryView from '@/views/QueryHistoryView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/test-map',
      name: 'test-map',
      component: TestMapView,
      meta: { title: 'Map Test' },
    },
    {
      path: '/',
      name: 'home',
      component: HomeView,
      meta: { title: 'SKTAQ Task Center' },
    },
    {
      path: '/app',
      component: AppLayout,
      children: [
        {
          path: '',
          redirect: { name: 'demo' },
        },
        // DATA OWNER
        {
          path: 'config',
          name: 'config',
          component: ConfigView,
          meta: { title: 'System Configuration', role: 'DATA OWNER', roleLabel: 'Data Provider' },
        },
        {
          path: 'data-manage',
          name: 'data-manage',
          component: DataManagementView,
          meta: { title: 'Data Management', role: 'DATA OWNER', roleLabel: 'Data Provider' },
        },
        // MOBILE USER
        {
          path: 'demo',
          name: 'demo',
          component: DemoView,
          meta: { title: 'Query Map', role: 'MOBILE USER', roleLabel: 'Query Terminal' },
        },
        {
          path: 'query-history',
          name: 'query-history',
          component: QueryHistoryView,
          meta: { title: 'Query History', role: 'MOBILE USER', roleLabel: 'Query Terminal' },
        },
        // SYSTEM ADMIN
        {
          path: 'dashboard',
          name: 'dashboard',
          component: DashboardView,
          meta: { title: 'Node Monitoring', role: 'SYSTEM ADMIN', roleLabel: 'System Monitor' },
        },
        {
          path: 'analysis',
          name: 'analysis',
          component: ResultsAnalysisView,
          meta: { title: 'Results Analysis', role: 'SYSTEM ADMIN', roleLabel: 'System Monitor' },
        },
      ],
    },
  ],
})

// Route guard: Set page title
router.beforeEach((to, from, next) => {
  if (to.meta.title) {
    document.title = `${to.meta.title} - SKTAQ`
  }
  next()
})

export default router
