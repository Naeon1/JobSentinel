<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Delete } from '@element-plus/icons-vue'
import { emailLogApi } from '../api'

// 数据
const logs = ref<any[]>([])
const loading = ref(false)

// 筛选条件
const filters = ref({
  status: '',
  trigger_type: '',
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
  { label: '发送成功', value: 'success' },
  { label: '发送失败', value: 'failed' },
  { label: '已跳过', value: 'skipped' },
]

// 触发来源选项
const triggerOptions = [
  { label: '全部', value: '' },
  { label: '手动触发', value: 'manual' },
  { label: '定时触发', value: 'scheduled' },
]

// 获取列表
const fetchLogs = async () => {
  loading.value = true
  try {
    const params: Record<string, any> = {
      skip: (pagination.value.page - 1) * pagination.value.size,
      limit: pagination.value.size,
    }
    if (filters.value.status) params.status = filters.value.status
    if (filters.value.trigger_type) params.trigger_type = filters.value.trigger_type

    const data = await emailLogApi.list(params) as any
    logs.value = data.items || []
    pagination.value.total = data.total || 0
  } catch (error) {
    console.error('获取邮件通知记录失败:', error)
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.value.page = 1
  fetchLogs()
}

// 重置筛选
const resetFilters = () => {
  filters.value = { status: '', trigger_type: '' }
  handleSearch()
}

// 删除单条
const deleteLog = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要删除该条记录吗？', '警告', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'error',
    })
    await emailLogApi.delete(row.id)
    ElMessage.success('已删除')
    fetchLogs()
  } catch (error) {
    // 用户取消
  }
}

// 获取状态类型
const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    success: 'success',
    failed: 'danger',
    skipped: 'info',
  }
  return map[status] || 'info'
}

// 获取状态文本
const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    success: '发送成功',
    failed: '发送失败',
    skipped: '已跳过',
  }
  return map[status] || status
}

// 获取触发来源文本
const getTriggerText = (type: string) => {
  const map: Record<string, string> = {
    manual: '手动触发',
    scheduled: '定时触发',
  }
  return map[type] || type
}

// 获取触发来源标签类型
const getTriggerType = (type: string) => {
  return type === 'manual' ? 'warning' : 'primary'
}

// 格式化日期
const formatDate = (date: string) => {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN')
}

// 收件人列表展示
const formatRecipients = (recipients: string[]) => {
  if (!recipients || !recipients.length) return '-'
  return recipients.join(', ')
}

// 分页变化
const handlePageChange = (page: number) => {
  pagination.value.page = page
  fetchLogs()
}

const handleSizeChange = (size: number) => {
  pagination.value.size = size
  pagination.value.page = 1
  fetchLogs()
}

onMounted(fetchLogs)
</script>

<template>
  <div class="email-log">
    <!-- 页面标题栏 -->
    <div class="page-header">
      <div class="header-info">
        <h2 class="page-title">邮件通知</h2>
        <p class="page-desc">查看每次搜索报告邮件的发送结果</p>
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

      <div class="filter-item">
        <label>触发来源</label>
        <el-select
          v-model="filters.trigger_type"
          placeholder="全部"
          clearable
          style="width: 130px"
        >
          <el-option
            v-for="item in triggerOptions"
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

    <!-- 表格 -->
    <div class="table-card">
      <el-table :data="logs" v-loading="loading" stripe>
        <el-table-column label="触发来源" width="110">
          <template #default="{ row }">
            <el-tag :type="getTriggerType(row.trigger_type) as any" size="small" round>
              {{ getTriggerText(row.trigger_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status) as any" size="small" round>
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="subject" label="邮件主题" min-width="220" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="subject-text">{{ row.subject || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="收件人" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="recipients-text">{{ formatRecipients(row.recipients) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="task_count" label="任务数" width="80" align="center" />
        <el-table-column prop="job_count" label="岗位数" width="80" align="center">
          <template #default="{ row }">
            <span class="job-count">{{ row.job_count ?? 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column label="耗时" width="90" align="center">
          <template #default="{ row }">
            <span class="duration-text">{{ row.duration_ms ?? 0 }} ms</span>
          </template>
        </el-table-column>
        <el-table-column label="时间" width="170">
          <template #default="{ row }">
            <span class="time-text">{{ formatDate(row.created_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="错误信息" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.error_message" class="error-text">{{ row.error_message }}</span>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }">
            <button class="action-btn danger" @click="deleteLog(row)">
              <el-icon :size="14"><Delete /></el-icon>
            </button>
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
  </div>
</template>

<style scoped>
.email-log {
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

.subject-text {
  font-size: 13px;
  color: var(--js-text-primary);
  font-weight: 500;
}

.recipients-text {
  font-size: 13px;
  color: var(--js-text-secondary);
}

.job-count {
  font-weight: 700;
  color: var(--js-primary);
}

.duration-text {
  font-size: 13px;
  font-weight: 600;
  color: var(--js-text-primary);
}

.time-text {
  font-size: 13px;
  color: var(--js-text-secondary);
}

.error-text {
  font-size: 13px;
  color: var(--js-danger);
}

.muted {
  color: var(--js-text-tertiary);
}

/* ── 操作按钮 ── */
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
</style>
