/**
 * 路由配置
 */

import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/dashboard',
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: () => import('../views/Dashboard.vue'),
      meta: { title: '仪表盘' },
    },
    {
      path: '/companies',
      name: 'Companies',
      component: () => import('../views/CompanyManage.vue'),
      meta: { title: '公司管理' },
    },
    {
      path: '/positions',
      name: 'Positions',
      component: () => import('../views/PositionConfig.vue'),
      meta: { title: '职位配置' },
    },
    {
      path: '/jobs',
      name: 'Jobs',
      component: () => import('../views/JobList.vue'),
      meta: { title: '招聘信息' },
    },
    {
      path: '/tasks',
      name: 'Tasks',
      component: () => import('../views/TaskHistory.vue'),
      meta: { title: '任务历史' },
    },
    {
      path: '/executions',
      name: 'Executions',
      component: () => import('../views/ExecutionDetail.vue'),
      meta: { title: '执行过程' },
    },
    {
      path: '/email-logs',
      name: 'EmailLogs',
      component: () => import('../views/EmailLog.vue'),
      meta: { title: '邮件通知' },
    },
    {
      path: '/settings',
      name: 'Settings',
      component: () => import('../views/Settings.vue'),
      meta: { title: '系统设置' },
    },
  ],
})

// 路由守卫 - 设置页面标题
router.beforeEach((to, from, next) => {
  const title = to.meta.title as string
  if (title) {
    document.title = `${title} - JobSentinel`
  }
  next()
})

export default router
