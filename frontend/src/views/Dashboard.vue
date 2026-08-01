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

onMounted(() => {
  fetchStats()
  fetchRecentTasks()
})
</script>

<template>
  <div class="dashboard" v-loading="loading">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-cards">
      <el-col :xs="12" :sm="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-item">
            <el-icon class="stat-icon" :size="40" color="#409eff">
              <OfficeBuilding />
            </el-icon>
            <div class="stat-content">
              <div class="stat-value">{{ stats.company_count }}</div>
              <div class="stat-label">监控公司</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="12" :sm="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-item">
            <el-icon class="stat-icon" :size="40" color="#67c23a">
              <Document />
            </el-icon>
            <div class="stat-content">
              <div class="stat-value">{{ stats.job_count }}</div>
              <div class="stat-label">招聘信息</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="12" :sm="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-item">
            <el-icon class="stat-icon" :size="40" color="#e6a23c">
              <Plus />
            </el-icon>
            <div class="stat-content">
              <div class="stat-value">{{ stats.today_count }}</div>
              <div class="stat-label">今日新增</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="12" :sm="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-item">
            <el-icon class="stat-icon" :size="40" color="#909399">
              <Timer />
            </el-icon>
            <div class="stat-content">
              <div class="stat-value">{{ stats.task_count }}</div>
              <div class="stat-label">执行任务</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快捷操作 -->
    <el-card class="quick-actions">
      <template #header>
        <div class="card-header">
          <span>快捷操作</span>
        </div>
      </template>
      <el-space wrap>
        <el-button
          type="primary"
          :icon="Search"
          :loading="searching"
          @click="runSearch"
        >
          立即执行搜索
        </el-button>
        <el-button @click="router.push('/companies')">
          管理公司
        </el-button>
        <el-button @click="router.push('/positions')">
          配置职位
        </el-button>
        <el-button @click="router.push('/jobs')">
          查看结果
        </el-button>
      </el-space>
    </el-card>

    <!-- 最近任务 -->
    <el-card class="recent-tasks">
      <template #header>
        <div class="card-header">
          <span>最近任务</span>
          <el-button text @click="router.push('/tasks')">查看全部</el-button>
        </div>
      </template>

      <el-table :data="recentTasks" stripe>
        <el-table-column prop="company_name" label="公司" width="120" />
        <el-table-column prop="position_title" label="职位" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status) as any">
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
    </el-card>
  </div>
</template>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.stat-cards {
  margin-bottom: 0;
}

.stat-card {
  height: 100%;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  flex-shrink: 0;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.quick-actions {
  margin-bottom: 0;
}

.recent-tasks {
  margin-bottom: 0;
}
</style>
