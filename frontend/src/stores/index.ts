/**
 * Pinia状态管理
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'

// 应用全局状态
export const useAppStore = defineStore('app', () => {
  // 侧边栏是否折叠
  const sidebarCollapsed = ref(false)

  // 切换侧边栏
  const toggleSidebar = () => {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  return {
    sidebarCollapsed,
    toggleSidebar,
  }
})

// 公司状态
export const useCompanyStore = defineStore('company', () => {
  const companies = ref<any[]>([])
  const loading = ref(false)

  return {
    companies,
    loading,
  }
})

// 招聘信息状态
export const useJobStore = defineStore('job', () => {
  const jobs = ref<any[]>([])
  const loading = ref(false)
  const total = ref(0)

  return {
    jobs,
    loading,
    total,
  }
})
