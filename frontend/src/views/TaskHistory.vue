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
    <!-- 页面标题栏 -->
    <div class="page-header">
      <div class="header-info">
        <h2 class="page-title">任务历史</h2>
        <p class="page-desc">查看和管理搜索任务的执行记录</p>
      </div>
      <div class="header-actions">
        <button
          v-if="selectedTasks.length"
          class="batch-delete-btn"
          @click="batchDeleteTasks"
        >
          <el-icon :size="14"><Delete /></el-icon>
          <span>批量删除 ({{ selectedTasks.length }})</span>
        </button>
      </div>
    </div>

    <!-- 筛选条件 -->
    <div class="filter-bar">
      <div class="filter-item">
        <label>状态</label>
        <el-select
          v-model="filters.status"
          placeholder="全部"
          clearable
          style="width: 130px"
        >
          <el-option
            v-for="item in statusOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
      </div>

      <div class="filter-actions">
        <button class="filter-btn primary" @click="handleSearch">
          <el-icon :size="14"><Search /></el-icon>
          <span>搜索</span>
        </button>
        <button class="filter-btn" @click="resetFilters">
          <el-icon :size="14"><Refresh /></el-icon>
          <span>重置</span>
        </button>
      </div>
    </div>

    <!-- 任务表格 -->
    <div class="table-card">
      <el-table
        :data="tasks"
        v-loading="loading"
        stripe
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="50" />
        <el-table-column prop="company_name" label="公司" width="140" />
        <el-table-column prop="position_title" label="职位" width="140" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status) as any" size="small" round>
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="jobs_found" label="找到职位" width="100">
          <template #default="{ row }">
            <span class="job-count">{{ row.jobs_found ?? 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column label="开始时间" width="170">
          <template #default="{ row }">
            <span class="time-text">{{ formatDate(row.started_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="完成时间" width="170">
          <template #default="{ row }">
            <span class="time-text">{{ formatDate(row.completed_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="耗时" width="90">
          <template #default="{ row }">
            <span class="duration-text">{{ getDuration(row) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <div class="action-btns">
              <button class="action-btn" @click="viewDetail(row)">
                <el-icon :size="14"><View /></el-icon>
              </button>
              <button class="action-btn danger" @click="deleteTask(row)">
                <el-icon :size="14"><Delete /></el-icon>
              </button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </div>

    <!-- 详情对话框 -->
    <el-dialog
      v-model="detailVisible"
      title="任务详情"
      width="620px"
      destroy-on-close
    >
      <div v-if="currentTask" class="task-detail">
        <div class="detail-meta">
          <div class="meta-item">
            <span class="meta-label">公司</span>
            <span class="meta-value">{{ currentTask.company_name }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">职位</span>
            <span class="meta-value">{{ currentTask.position_title }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">状态</span>
            <el-tag :type="getStatusType(currentTask.status) as any" size="small" round>
              {{ getStatusText(currentTask.status) }}
            </el-tag>
          </div>
          <div class="meta-item">
            <span class="meta-label">找到职位</span>
            <span class="meta-value highlight">{{ currentTask.jobs_found ?? 0 }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">耗时</span>
            <span class="meta-value">{{ getDuration(currentTask) }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">开始时间</span>
            <span class="meta-value">{{ formatDate(currentTask.started_at) }}</span>
          </div>
        </div>

        <!-- 执行步骤进度 -->
        <div class="step-section">
          <h4>执行步骤</h4>
          <el-progress
            :percentage="currentTask.progress || 0"
            :status="currentTask.status === 'failed' ? 'exception' : (currentTask.status === 'completed' ? 'success' : '')"
            :stroke-width="10"
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
        <button class="dialog-btn" @click="detailVisible = false">关闭</button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.task-history {
  max-width: 1200px;
  margin: 0 auto;
}

/* ── 页面标题栏 ── */
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 20px;
}

.header-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.page-title {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: var(--js-text-primary);
  letter-spacing: -0.02em;
}

.page-desc {
  margin: 0;
  font-size: 13px;
  color: var(--js-text-secondary);
}

.header-actions {
  display: flex;
  gap: 12px;
}

.batch-delete-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: rgba(239, 68, 68, 0.1);
  color: var(--js-danger);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: var(--js-radius-sm);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--js-transition);
}

.batch-delete-btn:hover {
  background: rgba(239, 68, 68, 0.15);
}

/* ── 筛选栏 ── */
.filter-bar {
  display: flex;
  align-items: flex-end;
  gap: 16px;
  padding: 16px 20px;
  background: var(--js-card-bg);
  border: 1px solid var(--js-card-border);
  border-radius: var(--js-radius-lg);
  margin-bottom: 16px;
  box-shadow: var(--js-card-shadow);
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.filter-item label {
  font-size: 12px;
  font-weight: 500;
  color: var(--js-text-secondary);
}

.filter-actions {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

.filter-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: var(--js-card-bg);
  border: 1px solid var(--js-card-border);
  border-radius: var(--js-radius-sm);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  color: var(--js-text-primary);
  transition: all var(--js-transition);
}

.filter-btn:hover {
  background: var(--js-page-bg);
}

.filter-btn.primary {
  background: var(--js-primary);
  border-color: var(--js-primary);
  color: #fff;
}

.filter-btn.primary:hover {
  background: var(--js-primary-light);
  border-color: var(--js-primary-light);
}

/* ── 表格卡片 ── */
.table-card {
  background: var(--js-card-bg);
  border: 1px solid var(--js-card-border);
  border-radius: var(--js-radius-lg);
  overflow: hidden;
  box-shadow: var(--js-card-shadow);
}

.job-count {
  font-weight: 700;
  color: var(--js-primary);
}

.time-text {
  font-size: 13px;
  color: var(--js-text-secondary);
}

.duration-text {
  font-weight: 600;
  color: var(--js-text-primary);
}

.action-btns {
  display: flex;
  gap: 4px;
}

.action-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  color: var(--js-text-secondary);
  transition: all var(--js-transition);
}

.action-btn:hover {
  background: var(--js-page-bg);
  color: var(--js-text-primary);
}

.action-btn.danger:hover {
  background: rgba(239, 68, 68, 0.1);
  color: var(--js-danger);
}

/* ── 分页 ── */
.pagination-wrap {
  padding: 16px 20px;
  border-top: 1px solid var(--js-card-border);
  display: flex;
  justify-content: flex-end;
}

/* ── 详情对话框 ── */
.task-detail {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.detail-meta {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  padding: 16px;
  background: var(--js-page-bg);
  border-radius: var(--js-radius-md);
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.meta-label {
  font-size: 12px;
  color: var(--js-text-tertiary);
  font-weight: 500;
}

.meta-value {
  font-size: 14px;
  color: var(--js-text-primary);
  font-weight: 500;
}

.meta-value.highlight {
  color: var(--js-primary);
  font-size: 18px;
  font-weight: 700;
}

.step-section h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 700;
  color: var(--js-text-primary);
}

.detail-steps {
  margin-top: 14px;
}

.step-msgs {
  margin-top: 14px;
  background: var(--js-page-bg);
  padding: 14px;
  border-radius: var(--js-radius-md);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.step-msg-row {
  font-size: 13px;
  line-height: 1.6;
}

.step-msg-title {
  font-weight: 700;
  color: var(--js-text-primary);
}

.step-msg-text {
  color: var(--js-text-secondary);
}

.error-section h4 {
  margin: 0 0 10px 0;
  font-size: 14px;
  font-weight: 700;
  color: var(--js-text-primary);
}

/* ── 对话框按钮 ── */
.dialog-btn {
  padding: 10px 20px;
  border-radius: var(--js-radius-sm);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  background: transparent;
  border: 1px solid var(--js-card-border);
  color: var(--js-text-secondary);
  transition: all var(--js-transition);
}

.dialog-btn:hover {
  background: var(--js-page-bg);
  color: var(--js-text-primary);
}
</style>
