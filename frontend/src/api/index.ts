/**
 * API配置
 */

import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建axios实例
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 可以在这里添加token等认证信息
    // const token = localStorage.getItem('token')
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`
    // }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    // 错误处理
    const message = error.response?.data?.detail || error.message || '请求失败'
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

export default api

// ==================== 公司API ====================

export const companyApi = {
  /** 获取公司列表 */
  list(params?: { skip?: number; limit?: number; is_active?: boolean; keyword?: string }) {
    return api.get('/api/companies/', { params })
  },

  /** 获取公司详情 */
  get(id: string) {
    return api.get(`/api/companies/${id}`)
  },

  /** 创建公司 */
  create(data: {
    name: string
    aliases?: string[]
    website?: string
    career_page?: string
    industry?: string
    notes?: string
  }) {
    return api.post('/api/companies/', data)
  },

  /** 更新公司 */
  update(id: string, data: Record<string, any>) {
    return api.put(`/api/companies/${id}`, data)
  },

  /** 删除公司（软删除/禁用） */
  delete(id: string) {
    return api.delete(`/api/companies/${id}`)
  },

  /** 启用公司 */
  enable(id: string) {
    return api.patch(`/api/companies/${id}/enable`)
  },

  /** 彻底删除公司 */
  hardDelete(id: string) {
    return api.delete(`/api/companies/${id}/hard`)
  },
}

// ==================== 职位配置API ====================

export const positionApi = {
  /** 获取职位配置列表 */
  list(params?: { skip?: number; limit?: number; is_active?: boolean; keyword?: string }) {
    return api.get('/api/positions/', { params })
  },

  /** 获取职位配置详情 */
  get(id: string) {
    return api.get(`/api/positions/${id}`)
  },

  /** 创建职位配置 */
  create(data: {
    title: string
    keywords?: string[]
    exclude_keywords?: string[]
    locations?: string[]
    experience_level?: string
  }) {
    return api.post('/api/positions/', data)
  },

  /** 更新职位配置 */
  update(id: string, data: Record<string, any>) {
    return api.put(`/api/positions/${id}`, data)
  },

  /** 删除职位配置（软删除/禁用） */
  delete(id: string) {
    return api.delete(`/api/positions/${id}`)
  },

  /** 启用职位配置 */
  enable(id: string) {
    return api.patch(`/api/positions/${id}/enable`)
  },

  /** 彻底删除职位配置 */
  hardDelete(id: string) {
    return api.delete(`/api/positions/${id}/hard`)
  },
}

// ==================== 招聘信息API ====================

export const jobApi = {
  /** 获取招聘信息列表 */
  list(params?: {
    skip?: number
    limit?: number
    company_id?: string
    keyword?: string
    location?: string
    salary_min?: number
    salary_max?: number
    source_platform?: string
    is_verified?: boolean
  }) {
    return api.get('/api/jobs/', { params })
  },

  /** 获取招聘信息详情 */
  get(id: string) {
    return api.get(`/api/jobs/${id}`)
  },

  /** 删除招聘信息 */
  delete(id: string) {
    return api.delete(`/api/jobs/${id}`)
  },
}

// ==================== 任务API ====================

export const taskApi = {
  /** 获取任务列表 */
  list(params?: {
    skip?: number
    limit?: number
    status?: string
    company_id?: string
  }) {
    return api.get('/api/tasks/', { params })
  },

  /** 获取任务详情 */
  get(id: string) {
    return api.get(`/api/tasks/${id}`)
  },

  /** 手动触发搜索 */
  run(data?: { company_id?: string; position_id?: string }) {
    return api.post('/api/tasks/run', data)
  },

  /** 删除任务 */
  delete(id: string) {
    return api.delete(`/api/tasks/${id}`)
  },
}

// ==================== 仪表盘API ====================

export const dashboardApi = {
  /** 获取统计数据 */
  getStats() {
    return api.get('/api/dashboard/stats')
  },
}

// ==================== 定时任务API ====================

export const scheduleApi = {
  /** 获取当前配置 */
  getCurrent() {
    return api.get('/api/schedules/current')
  },

  /** 更新配置 */
  updateCurrent(data: { cron_expression?: string; is_enabled?: boolean }) {
    return api.put('/api/schedules/current', data)
  },

  /** 直接预览某 Cron 表达式的下次执行时间（前端本地解析，不调后端） */
  // 注：后端 GET /current 已返回 next_run_at，无需单独接口
}

// ==================== 配置测试API ====================

export const configTestApi = {
  /** 获取邮件配置状态（不返回密码） */
  getEmailConfig() {
    return api.get('/api/email/config')
  },

  /** 发送测试邮件 */
  sendTestEmail(data?: { recipients?: string[] }) {
    return api.post('/api/email/test', data || {})
  },
}

// ==================== 邮件通知记录API ====================

export const emailLogApi = {
  /** 获取邮件通知记录列表 */
  list(params?: {
    skip?: number
    limit?: number
    status?: string
    trigger_type?: string
  }) {
    return api.get('/api/email-logs/', { params })
  },

  /** 删除单条邮件通知记录 */
  delete(id: string) {
    return api.delete(`/api/email-logs/${id}`)
  },
}
