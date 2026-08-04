<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  OfficeBuilding,
  Document,
  Plus,
  Timer,
  Search,
  ArrowRight,
} from '@element-plus/icons-vue'
import { dashboardApi, taskApi } from '../api'

const router = useRouter()
const loading = ref(false)
const searching = ref(false)

// 统计数据
const stats = ref({
  company_count: 0,
  job_count: 0,
  today_count: 0,
  task_count: 0,
})

// 最近任务
const recentTasks = ref<any[]>([])

// 获取统计数据
const fetchStats = async () => {
  loading.value = true
  try {
    const data = await dashboardApi.getStats()
    stats.value = data as any
  } catch (error) {
    console.error('获取统计数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 获取最近任务
const fetchRecentTasks = async () => {
  try {
    const data = await taskApi.list({ limit: 5 }) as any
    recentTasks.value = data.items || []
  } catch (error) {
    console.error('获取任务列表失败:', error)
  }
}

// 手动触发搜索 → 跳转执行过程页
const runSearch = async () => {
  searching.value = true
  try {
    const data = await taskApi.run() as any
    const ids: string[] = data?.task_ids || []
    if (!ids.length) {
      ElMessage.warning('没有可执行的公司×职位组合')
      searching.value = false
      return
    }
    ElMessage.success(`已启动 ${ids.length} 个任务`)
    router.push({ path: '/executions', query: { ids: ids.join(',') } })
  } catch (error) {
    console.error('启动搜索失败:', error)
  } finally {
    searching.value = false
  }
}

// 获取状态类型
const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    pending: 'info',
    planning: 'warning',
    planning_searching: 'warning',
    searching: 'warning',
    extracting: 'warning',
    running: 'warning',
    completed: 'success',
    failed: 'danger',
  }
  return map[status] || 'info'
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    pending: '待执行',
    planning: '规划中',
    searching: '搜索中',
    extracting: '梳理中',
    running: '执行中',
    completed: '已完成',
    failed: '失败',
  }
  return map[status] || status
}

// 格式化日期
const formatDate = (date: string) => {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN')
}

// 统计卡片配置
const statCards = [
  {
    key: 'company_count',
    label: '监控公司',
    gradient: 'var(--js-gradient-blue)',
    icon: OfficeBuilding,
    color: '#3b82f6',
  },
  {
    key: 'job_count',
    label: '招聘信息',
    gradient: 'var(--js-gradient-green)',
    icon: Document,
    color: '#10b981',
  },
  {
    key: 'today_count',
    label: '今日新增',
    gradient: 'var(--js-gradient-orange)',
    icon: Plus,
    color: '#f59e0b',
  },
  {
    key: 'task_count',
    label: '执行任务',
    gradient: 'var(--js-gradient-purple)',
    icon: Timer,
    color: '#6366f1',
  },
]

onMounted(() => {
  fetchStats()
  fetchRecentTasks()
})
</script>

<template>
  <div class="dashboard" v-loading="loading">
    <!-- 统计卡片 -->
    <div class="stat-grid">
      <div
        v-for="card in statCards"
        :key="card.key"
        class="stat-card"
      >
        <div class="stat-card-bg" :style="{ background: card.gradient }"></div>
        <div class="stat-card-content">
          <div class="stat-icon-wrap" :style="{ color: card.color }">
            <el-icon :size="24">
              <component :is="card.icon" />
            </el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats[card.key as keyof typeof stats] }}</div>
            <div class="stat-label">{{ card.label }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 快捷操作区 -->
    <div class="action-section">
      <div class="section-header">
        <h2 class="section-title">快捷操作</h2>
      </div>
      <div class="action-cards">
        <!-- 主操作卡片：执行搜索 -->
        <button class="action-card primary" @click="runSearch" :disabled="searching">
          <div class="action-icon">
            <el-icon :size="28"><Search /></el-icon>
          </div>
          <div class="action-info">
            <div class="action-title">立即执行搜索</div>
            <div class="action-desc">运行 LLM 三阶段搜索流水线</div>
          </div>
          <el-icon v-if="!searching" :size="20" class="action-arrow"><ArrowRight /></el-icon>
          <div v-if="searching" class="action-loading">
            <div class="spinner"></div>
          </div>
        </button>

        <!-- 次要操作 -->
        <div class="action-secondary">
          <button class="action-chip" @click="router.push('/companies')">
            <el-icon :size="16"><OfficeBuilding /></el-icon>
            <span>管理公司</span>
          </button>
          <button class="action-chip" @click="router.push('/positions')">
            <el-icon :size="16"><Document /></el-icon>
            <span>配置职位</span>
          </button>
          <button class="action-chip" @click="router.push('/jobs')">
            <el-icon :size="16"><Timer /></el-icon>
            <span>查看结果</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 最近任务 -->
    <div class="tasks-section">
      <div class="section-header">
        <h2 class="section-title">最近任务</h2>
        <button class="view-all-btn" @click="router.push('/tasks')">
          查看全部 <el-icon :size="14"><ArrowRight /></el-icon>
        </button>
      </div>
      <div class="tasks-card">
        <el-table :data="recentTasks" stripe>
          <el-table-column prop="company_name" label="公司" width="140" />
          <el-table-column prop="position_title" label="职位" width="140" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status) as any" size="small" round>
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="jobs_found" label="找到职位" width="100" />
          <el-table-column label="完成时间">
            <template #default="{ row }">
              {{ formatDate(row.completed_at) }}
            </template>
          </el-table-column>
        </el-table>
        <el-empty
          v-if="!recentTasks.length"
          description="暂无任务记录"
          :image-size="80"
          style="padding: 40px 0"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard {
  max-width: 1200px;
  margin: 0 auto;
}

/* ── 统计卡片 ── */
.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 32px;
}

@media (max-width: 1024px) {
  .stat-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 640px) {
  .stat-grid { grid-template-columns: 1fr; }
}

.stat-card {
  position: relative;
  border-radius: var(--js-radius-lg);
  overflow: hidden;
  background: var(--js-card-bg);
  border: 1px solid var(--js-card-border);
  box-shadow: var(--js-card-shadow);
  transition: all var(--js-transition);
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--js-card-shadow-hover);
}

.stat-card-bg {
  position: absolute;
  top: 0;
  right: 0;
  width: 120px;
  height: 120px;
  opacity: 0.1;
  border-radius: 0 0 0 100%;
  transform: translate(20%, -20%);
}

.stat-card-content {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  position: relative;
  z-index: 1;
}

.stat-icon-wrap {
  width: 52px;
  height: 52px;
  border-radius: var(--js-radius-md);
  background: var(--js-card-bg);
  border: 1px solid var(--js-card-border);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--js-text-primary);
  line-height: 1.1;
  letter-spacing: -0.02em;
}

.stat-label {
  font-size: 13px;
  color: var(--js-text-secondary);
  font-weight: 500;
}

/* ── 操作区 ── */
.action-section {
  margin-bottom: 32px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.section-title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: var(--js-text-primary);
  letter-spacing: -0.01em;
}

.view-all-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  border: none;
  background: transparent;
  color: var(--js-primary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  padding: 4px 0;
  transition: all var(--js-transition);
}

.view-all-btn:hover {
  color: var(--js-primary-light);
}

.action-cards {
  display: flex;
  gap: 16px;
  align-items: stretch;
}

.action-card.primary {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 24px;
  background: linear-gradient(135deg, #1e40af 0%, #3b82f6 50%, #60a5fa 100%);
  border: none;
  border-radius: var(--js-radius-lg);
  cursor: pointer;
  color: #ffffff;
  text-align: left;
  transition: all var(--js-transition);
  position: relative;
  overflow: hidden;
}

.action-card.primary::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -20%;
  width: 200px;
  height: 200px;
  background: rgba(255,255,255,0.1);
  border-radius: 50%;
}

.action-card.primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(59, 130, 246, 0.4);
}

.action-card.primary:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.action-icon {
  width: 56px;
  height: 56px;
  border-radius: var(--js-radius-md);
  background: rgba(255,255,255,0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.action-info {
  flex: 1;
}

.action-title {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 4px;
}

.action-desc {
  font-size: 13px;
  opacity: 0.8;
}

.action-arrow {
  opacity: 0.7;
  transition: all var(--js-transition);
}

.action-card.primary:hover .action-arrow {
  opacity: 1;
  transform: translateX(4px);
}

.action-loading {
  width: 24px;
  height: 24px;
}

.spinner {
  width: 24px;
  height: 24px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.action-secondary {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.action-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: var(--js-card-bg);
  border: 1px solid var(--js-card-border);
  border-radius: var(--js-radius-md);
  cursor: pointer;
  color: var(--js-text-primary);
  font-size: 13px;
  font-weight: 500;
  transition: all var(--js-transition);
  white-space: nowrap;
}

.action-chip:hover {
  background: var(--js-primary-alpha);
  border-color: var(--js-primary);
  color: var(--js-primary);
}

/* ── 任务区 ── */
.tasks-section {
  margin-bottom: 32px;
}

.tasks-card {
  background: var(--js-card-bg);
  border: 1px solid var(--js-card-border);
  border-radius: var(--js-radius-lg);
  overflow: hidden;
  box-shadow: var(--js-card-shadow);
}
</style>
