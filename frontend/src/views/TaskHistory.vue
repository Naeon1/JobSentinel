<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, View, Delete } from '@element-plus/icons-vue'
import { taskApi } from '../api'

// 数据
const tasks = ref<any[]>([])
const loading = ref(false)
const detailVisible = ref(false)
const currentTask = ref<any>(null)
const selectedTasks = ref<any[]>([])

// 多选变化
const handleSelectionChange = (rows: any[]) => {
  selectedTasks.value = rows
}

// 删除单个任务
const deleteTask = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除该任务吗？`,
      '警告',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'error' }
    )
    await taskApi.delete(row.id)
    ElMessage.success('已删除')
    fetchTasks()
  } catch (error) {
    // 用户取消
  }
}

// 批量删除任务
const batchDeleteTasks = async () => {
  if (!selectedTasks.value.length) {
    ElMessage.warning('请先选择要删除的任务')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedTasks.value.length} 个任务吗？`,
      '警告',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'error' }
    )
    const ids = selectedTasks.value.map((r) => r.id)
    await Promise.all(ids.map((id) => taskApi.delete(id)))
    ElMessage.success(`已删除 ${ids.length} 个任务`)
    selectedTasks.value = []
    fetchTasks()
  } catch (error) {
    // 用户取消
  }
}

// 自动刷新轮询（列表含进行中任务时启用）
const refreshTimer = ref<any>(null)

// 筛选条件
const filters = ref({
  status: '',
  company_id: '',
})

// 分页
const pagination = ref({
  page: 1,
  size: 20,
  total: 0,
})

// 状态选项
const statusOptions = [
  { label: '全部', value: '' },
  { label: '规划中', value: 'planning' },
  { label: '搜索中', value: 'searching' },
  { label: '梳理中', value: 'extracting' },
  { label: '执行中', value: 'running' },
  { label: '已完成', value: 'completed' },
  { label: '失败', value: 'failed' },
]

// 进行中状态集合
const ACTIVE_STATUS = ['planning', 'searching', 'extracting', 'running']
const phaseDefs = [
  { key: 'planning', title: '生成策略' },
  { key: 'searching', title: '搜索' },
  { key: 'extracting', title: '梳理结果' },
]

// 获取任务列表
const fetchTasks = async () => {
  loading.value = true
  try {
    const params: Record<string, any> = {
      skip: (pagination.value.page - 1) * pagination.value.size,
      limit: pagination.value.size,
    }

    if (filters.value.status) params.status = filters.value.status
    if (filters.value.company_id) params.company_id = filters.value.company_id

    const data = await taskApi.list(params) as any
    tasks.value = data.items || []
    pagination.value.total = data.total || 0
    // 根据是否有进行中任务启停轮询
    updateAutoRefresh()
  } catch (error) {
    console.error('获取任务列表失败:', error)
  } finally {
    loading.value = false
  }
}

const updateAutoRefresh = () => {
  const hasActive = tasks.value.some((t) => ACTIVE_STATUS.includes(t.status))
  if (hasActive && !refreshTimer.value) {
    refreshTimer.value = setInterval(fetchTasks, 3000)
  } else if (!hasActive && refreshTimer.value) {
    clearInterval(refreshTimer.value)
    refreshTimer.value = null
  }
}

// 搜索
const handleSearch = () => {
  pagination.value.page = 1
  fetchTasks()
}

// 重置筛选
const resetFilters = () => {
  filters.value = {
    status: '',
    company_id: '',
  }
  handleSearch()
}

// 查看详情
const viewDetail = async (row: any) => {
  try {
    const data = await taskApi.get(row.id)
    currentTask.value = data
    detailVisible.value = true
  } catch (error) {
    console.error('获取任务详情失败:', error)
  }
}

// 详情里单条步骤的阶段文案
const phaseMessage = (key: string, task: any) => {
  const logs: any[] = task?.steps_log || []
  let last = ''
  for (const log of logs) {
    if (log.step === key) last = log.message
  }
  return last
}

// 详情里阶段状态
const phaseStatusFor = (key: string, task: any) => {
  if (!task) return 'wait'
  const order = ['planning', 'searching', 'extracting', 'done']
  const cur = order.indexOf(task.current_step)
  const idx = order.indexOf(key)
  if (task.status === 'failed') {
    if (task.current_step === key) return 'error'
    if (idx < cur) return 'finish'
    return 'wait'
  }
  if (cur === -1) return 'wait'
  if (idx < cur) return 'finish'
  if (idx === cur) return 'process'
  if (task.current_step === 'done') return 'finish'
  return 'wait'
}

// 获取状态类型
const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    pending: 'info',
    planning: 'warning',
    searching: 'warning',
    extracting: 'warning',
    running: 'warning',
    completed: 'success',
    failed: 'danger',
  }
  return map[status] || 'info'
}

// 获取状态文本
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

// 计算耗时
const getDuration = (task: any) => {
  if (!task.started_at || !task.completed_at) return '-'
  const start = new Date(task.started_at).getTime()
  const end = new Date(task.completed_at).getTime()
  const seconds = Math.floor((end - start) / 1000)

  if (seconds < 60) return `${seconds}秒`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}分${seconds % 60}秒`
  return `${Math.floor(seconds / 3600)}时${Math.floor((seconds % 3600) / 60)}分`
}

// 分页变化
const handlePageChange = (page: number) => {
  pagination.value.page = page
  fetchTasks()
}

const handleSizeChange = (size: number) => {
  pagination.value.size = size
  pagination.value.page = 1
  fetchTasks()
}

onMounted(fetchTasks)

onBeforeUnmount(() => {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value)
    refreshTimer.value = null
  }
})
</script>

<template>
  <div class="task-history">
    <!-- 筛选条件 -->
    <el-card class="filter-card">
      <el-form :model="filters" inline>
        <el-form-item label="状态">
          <el-select
            v-model="filters.status"
            placeholder="选择状态"
            clearable
            style="width: 120px"
          >
            <el-option
              v-for="item in statusOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">
            搜索
          </el-button>
          <el-button :icon="Refresh" @click="resetFilters">
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 任务表格 -->
    <el-card>
      <template #header>
        <div class="table-header">
          <span>任务历史</span>
          <el-button
            v-if="selectedTasks.length"
            type="danger"
            :icon="Delete"
            @click="batchDeleteTasks"
          >
            批量删除（{{ selectedTasks.length }}）
          </el-button>
        </div>
      </template>
      <el-table :data="tasks" v-loading="loading" stripe @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="50" />
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
        <el-table-column label="开始时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.started_at) }}
          </template>
        </el-table-column>
        <el-table-column label="完成时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.completed_at) }}
          </template>
        </el-table-column>
        <el-table-column label="耗时" width="100">
          <template #default="{ row }">
            {{ getDuration(row) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              :icon="View"
              @click="viewDetail(row)"
            >
              详情
            </el-button>
            <el-button
              type="danger"
              link
              :icon="Delete"
              @click="deleteTask(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </el-card>

    <!-- 详情对话框 -->
    <el-dialog
      v-model="detailVisible"
      title="任务详情"
      width="600px"
    >
      <div v-if="currentTask" class="task-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="任务ID">
            {{ currentTask.id }}
          </el-descriptions-item>
          <el-descriptions-item label="公司">
            {{ currentTask.company_name }}
          </el-descriptions-item>
          <el-descriptions-item label="职位">
            {{ currentTask.position_title }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(currentTask.status) as any">
              {{ getStatusText(currentTask.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="找到职位">
            {{ currentTask.jobs_found }}
          </el-descriptions-item>
          <el-descriptions-item label="耗时">
            {{ getDuration(currentTask) }}
          </el-descriptions-item>
          <el-descriptions-item label="开始时间" :span="2">
            {{ formatDate(currentTask.started_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="完成时间" :span="2">
            {{ formatDate(currentTask.completed_at) }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 执行步骤进度 -->
        <div class="step-section">
          <h4>执行步骤</h4>
          <el-progress
            :percentage="currentTask.progress || 0"
            :status="currentTask.status === 'failed' ? 'exception' : (currentTask.status === 'completed' ? 'success' : '')"
            :stroke-width="12"
          />
          <el-steps :space="80" align-center class="detail-steps">
            <el-step
              v-for="p in phaseDefs"
              :key="p.key"
              :title="p.title"
              :status="phaseStatusFor(p.key, currentTask) as any"
            />
          </el-steps>
          <div class="step-msgs">
            <div v-for="p in phaseDefs" :key="p.key" class="step-msg-row">
              <span class="step-msg-title">{{ p.title }}：</span>
              <span class="step-msg-text">{{ phaseMessage(p.key, currentTask) || '—' }}</span>
            </div>
          </div>
        </div>

        <div v-if="currentTask.error_message" class="error-section">
          <h4>错误信息</h4>
          <el-alert
            :title="currentTask.error_message"
            type="error"
            :closable="false"
            show-icon
          />
        </div>
      </div>

      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.task-history {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-card {
  margin-bottom: 0;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.task-detail {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.step-section h4 {
  margin: 0 0 10px 0;
  font-size: 16px;
  color: #303133;
}

.detail-steps {
  margin-top: 14px;
}

.step-msgs {
  margin-top: 12px;
  background-color: #f5f7fa;
  padding: 12px 14px;
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.step-msg-row {
  font-size: 13px;
  line-height: 1.6;
}

.step-msg-title {
  font-weight: 600;
  color: #303133;
}

.step-msg-text {
  color: #606266;
}

.error-section h4 {
  margin: 0 0 10px 0;
  font-size: 16px;
  color: #303133;
}
</style>
