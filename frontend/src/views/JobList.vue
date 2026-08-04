<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, View, Link, Delete } from '@element-plus/icons-vue'
import { jobApi, companyApi } from '../api'

// 数据
const jobs = ref<any[]>([])
const companies = ref<any[]>([])
const loading = ref(false)
const detailVisible = ref(false)
const currentJob = ref<any>(null)
const selectedJobs = ref<any[]>([])

// 多选变化
const handleSelectionChange = (rows: any[]) => {
  selectedJobs.value = rows
}

// 批量删除
const batchDeleteJobs = async () => {
  if (!selectedJobs.value.length) {
    ElMessage.warning('请先选择要删除的招聘信息')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedJobs.value.length} 条招聘信息吗？`,
      '警告',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'error' }
    )
    const ids = selectedJobs.value.map((r) => r.id)
    await Promise.all(ids.map((id) => jobApi.delete(id)))
    ElMessage.success(`已删除 ${ids.length} 条`)
    selectedJobs.value = []
    fetchJobs()
  } catch (error) {
    // 用户取消
  }
}

// 筛选条件
const filters = ref({
  company_id: '',
  keyword: '',
  location: '',
  salary_min: undefined as number | undefined,
  salary_max: undefined as number | undefined,
  source_platform: '',
})

// 分页
const pagination = ref({
  page: 1,
  size: 20,
  total: 0,
})

// 薪资范围选项
const salaryRanges = [
  { label: '不限', min: undefined, max: undefined },
  { label: '10k以下', min: 0, max: 10000 },
  { label: '10k-20k', min: 10000, max: 20000 },
  { label: '20k-30k', min: 20000, max: 30000 },
  { label: '30k-50k', min: 30000, max: 50000 },
  { label: '50k以上', min: 50000, max: undefined },
]

// 获取招聘信息列表
const fetchJobs = async () => {
  loading.value = true
  try {
    const params: Record<string, any> = {
      skip: (pagination.value.page - 1) * pagination.value.size,
      limit: pagination.value.size,
    }

    if (filters.value.company_id) params.company_id = filters.value.company_id
    if (filters.value.keyword) params.keyword = filters.value.keyword
    if (filters.value.location) params.location = filters.value.location
    if (filters.value.salary_min) params.salary_min = filters.value.salary_min
    if (filters.value.salary_max) params.salary_max = filters.value.salary_max
    if (filters.value.source_platform) params.source_platform = filters.value.source_platform

    const data = await jobApi.list(params) as any
    jobs.value = data.items || []
    pagination.value.total = data.total || 0
  } catch (error) {
    console.error('获取招聘信息失败:', error)
  } finally {
    loading.value = false
  }
}

// 获取公司列表
const fetchCompanies = async () => {
  try {
    const data = await companyApi.list() as any
    companies.value = data.items || []
  } catch (error) {
    console.error('获取公司列表失败:', error)
  }
}

// 搜索
const handleSearch = () => {
  pagination.value.page = 1
  fetchJobs()
}

// 重置筛选
const resetFilters = () => {
  filters.value = {
    company_id: '',
    keyword: '',
    location: '',
    salary_min: undefined,
    salary_max: undefined,
    source_platform: '',
  }
  handleSearch()
}

// 薪资范围变化
const handleSalaryChange = (range: { min?: number; max?: number }) => {
  filters.value.salary_min = range.min
  filters.value.salary_max = range.max
}

// 查看详情
const viewDetail = (row: any) => {
  currentJob.value = row
  detailVisible.value = true
}

// 打开原文
const openSource = (row: any) => {
  if (row.source_url) {
    window.open(row.source_url, '_blank')
  } else {
    ElMessage.warning('暂无原文链接')
  }
}

// 删除招聘信息
const deleteJob = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除该招聘信息吗？`,
      '警告',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'error' }
    )
    await jobApi.delete(row.id)
    ElMessage.success('已删除')
    fetchJobs()
  } catch (error) {
    // 用户取消
  }
}

// 格式化日期
const formatDate = (date: string) => {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('zh-CN')
}

// 格式化薪资
const formatSalary = (row: any) => {
  if (row.salary_description) return row.salary_description
  if (row.salary_min && row.salary_max) {
    return `${(row.salary_min / 1000).toFixed(0)}k-${(row.salary_max / 1000).toFixed(0)}k`
  }
  if (row.salary_min) return `${(row.salary_min / 1000).toFixed(0)}k起`
  if (row.salary_max) return `最高${(row.salary_max / 1000).toFixed(0)}k`
  return '面议'
}

// 是否在招
const isOpenType = (v: string) => {
  if (v === 'true') return 'success'
  if (v === 'false') return 'danger'
  return 'info'
}
const isOpenText = (v: string) => {
  if (v === 'true') return '在招'
  if (v === 'false') return '疑似停招'
  return '不确定'
}

// 分页变化
const handlePageChange = (page: number) => {
  pagination.value.page = page
  fetchJobs()
}

const handleSizeChange = (size: number) => {
  pagination.value.size = size
  pagination.value.page = 1
  fetchJobs()
}

onMounted(() => {
  fetchCompanies()
  fetchJobs()
})
</script>

<template>
  <div class="job-list">
    <!-- 页面标题栏 -->
    <div class="page-header">
      <div class="header-info">
        <h2 class="page-title">招聘信息</h2>
        <p class="page-desc">查看和管理搜索到的招聘结果</p>
      </div>
      <div class="header-actions">
        <button
          v-if="selectedJobs.length"
          class="batch-delete-btn"
          @click="batchDeleteJobs"
        >
          <el-icon :size="14"><Delete /></el-icon>
          <span>批量删除 ({{ selectedJobs.length }})</span>
        </button>
      </div>
    </div>

    <!-- 筛选条件 -->
    <div class="filter-bar">
      <div class="filter-item">
        <label>公司</label>
        <el-select
          v-model="filters.company_id"
          clearable
          placeholder="全部公司"
          style="width: 160px"
        >
          <el-option
            v-for="company in companies"
            :key="company.id"
            :label="company.name"
            :value="company.id"
          />
        </el-select>
      </div>

      <div class="filter-item">
        <label>职位</label>
        <el-input
          v-model="filters.keyword"
          placeholder="搜索职位"
          clearable
          style="width: 140px"
          @keyup.enter="handleSearch"
        />
      </div>

      <div class="filter-item">
        <label>地点</label>
        <el-input
          v-model="filters.location"
          placeholder="工作地点"
          clearable
          style="width: 120px"
          @keyup.enter="handleSearch"
        />
      </div>

      <div class="filter-item">
        <label>薪资</label>
        <el-select
          placeholder="不限"
          style="width: 130px"
          @change="handleSalaryChange"
        >
          <el-option
            v-for="(range, index) in salaryRanges"
            :key="index"
            :label="range.label"
            :value="range"
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

    <!-- 招聘信息表格 -->
    <div class="table-card">
      <el-table
        :data="jobs"
        v-loading="loading"
        stripe
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="50" />
        <el-table-column prop="company_name" label="公司" width="140">
          <template #default="{ row }">
            <div class="company-cell">
              <div class="company-avatar">{{ row.company_name?.charAt(0) || '?' }}</div>
              <span>{{ row.company_name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="job_title" label="职位" min-width="160">
          <template #default="{ row }">
            <span class="job-title">{{ row.job_title }}</span>
          </template>
        </el-table-column>
        <el-table-column label="薪资" width="120">
          <template #default="{ row }">
            <span class="salary">{{ formatSalary(row) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="location" label="地点" width="100" />
        <el-table-column prop="experience_years" label="经验" width="80" />
        <el-table-column prop="education" label="学历" width="80" />
        <el-table-column label="在招" width="90">
          <template #default="{ row }">
            <el-tag :type="isOpenType(row.is_open)" size="small" round>
              {{ isOpenText(row.is_open) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="source_platform" label="来源" width="100">
          <template #default="{ row }">
            <span class="platform-badge">{{ row.source_platform || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="更新" width="110">
          <template #default="{ row }">
            {{ formatDate(row.crawled_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <div class="action-btns">
              <button class="action-btn" @click="viewDetail(row)">
                <el-icon :size="14"><View /></el-icon>
              </button>
              <button
                class="action-btn"
                :disabled="!row.source_url"
                @click="openSource(row)"
              >
                <el-icon :size="14"><Link /></el-icon>
              </button>
              <button class="action-btn danger" @click="deleteJob(row)">
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
      title="职位详情"
      width="700px"
      destroy-on-close
    >
      <div v-if="currentJob" class="job-detail">
        <div class="detail-header">
          <h3 class="detail-title">{{ currentJob.job_title }}</h3>
          <el-tag :type="isOpenType(currentJob.is_open)" size="default" round>
            {{ isOpenText(currentJob.is_open) }}
          </el-tag>
        </div>

        <div class="detail-meta">
          <div class="meta-item">
            <span class="meta-label">公司</span>
            <span class="meta-value">{{ currentJob.company_name }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">薪资</span>
            <span class="meta-value salary">{{ formatSalary(currentJob) }}</span>
          </div>
          <div class="meta-item" v-if="currentJob.location">
            <span class="meta-label">地点</span>
            <span class="meta-value">{{ currentJob.location }}</span>
          </div>
          <div class="meta-item" v-if="currentJob.experience_years">
            <span class="meta-label">经验</span>
            <span class="meta-value">{{ currentJob.experience_years }}</span>
          </div>
          <div class="meta-item" v-if="currentJob.education">
            <span class="meta-label">学历</span>
            <span class="meta-value">{{ currentJob.education }}</span>
          </div>
          <div class="meta-item" v-if="currentJob.source_platform">
            <span class="meta-label">来源</span>
            <span class="meta-value">{{ currentJob.source_platform }}</span>
          </div>
        </div>

        <div class="detail-url" v-if="currentJob.source_url">
          <span class="meta-label">原文链接</span>
          <a :href="currentJob.source_url" target="_blank" class="source-link">
            {{ currentJob.source_url }}
          </a>
        </div>

        <div v-if="currentJob.skills?.length" class="detail-section">
          <h4>技能要求 <span class="hint">（从搜索摘要提取，可能不完整）</span></h4>
          <div class="skills-wrap">
            <span v-for="skill in currentJob.skills" :key="skill" class="skill-tag">
              {{ skill }}
            </span>
          </div>
        </div>

        <div v-if="currentJob.job_description" class="detail-section">
          <h4>职位描述</h4>
          <div class="description">{{ currentJob.job_description }}</div>
        </div>

        <div v-if="currentJob.requirements" class="detail-section">
          <h4>任职要求</h4>
          <div class="description">{{ currentJob.requirements }}</div>
        </div>

        <div v-if="currentJob.benefits?.length" class="detail-section">
          <h4>福利待遇</h4>
          <div class="benefits-wrap">
            <span v-for="benefit in currentJob.benefits" :key="benefit" class="benefit-tag">
              {{ benefit }}
            </span>
          </div>
        </div>
      </div>

      <template #footer>
        <button class="dialog-btn cancel" @click="detailVisible = false">关闭</button>
        <button
          class="dialog-btn primary"
          @click="openSource(currentJob)"
          :disabled="!currentJob?.source_url"
        >
          查看原文
        </button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.job-list {
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
  flex-wrap: wrap;
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

.company-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.company-avatar {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: var(--js-primary-alpha);
  color: var(--js-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 12px;
  flex-shrink: 0;
}

.job-title {
  font-weight: 600;
  color: var(--js-text-primary);
}

.salary {
  color: #f59e0b;
  font-weight: 700;
}

.platform-badge {
  display: inline-flex;
  padding: 2px 8px;
  background: #f1f5f9;
  color: var(--js-text-secondary);
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
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

.action-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

/* ── 分页 ── */
.pagination-wrap {
  padding: 16px 20px;
  border-top: 1px solid var(--js-card-border);
  display: flex;
  justify-content: flex-end;
}

/* ── 详情对话框 ── */
.detail-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.detail-title {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: var(--js-text-primary);
}

.detail-meta {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 20px;
  padding: 16px;
  background: var(--js-page-bg);
  border-radius: var(--js-radius-md);
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
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

.meta-value.salary {
  color: #f59e0b;
}

.detail-url {
  margin-bottom: 20px;
}

.detail-url .meta-label {
  display: block;
  margin-bottom: 4px;
}

.source-link {
  color: var(--js-primary);
  word-break: break-all;
}

.detail-section {
  margin-bottom: 20px;
}

.detail-section h4 {
  margin: 0 0 10px 0;
  font-size: 14px;
  font-weight: 700;
  color: var(--js-text-primary);
}

.hint {
  font-size: 12px;
  color: var(--js-text-tertiary);
  font-weight: normal;
}

.skills-wrap,
.benefits-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.skill-tag {
  padding: 4px 10px;
  background: var(--js-primary-alpha);
  color: var(--js-primary);
  border-radius: 4px;
  font-size: 13px;
  font-weight: 500;
}

.benefit-tag {
  padding: 4px 10px;
  background: rgba(16, 185, 129, 0.1);
  color: var(--js-success);
  border-radius: 4px;
  font-size: 13px;
  font-weight: 500;
}

.description {
  white-space: pre-wrap;
  line-height: 1.7;
  color: var(--js-text-secondary);
  background: var(--js-page-bg);
  padding: 14px;
  border-radius: var(--js-radius-md);
  font-size: 13px;
}

/* ── 对话框按钮 ── */
.dialog-btn {
  padding: 10px 20px;
  border-radius: var(--js-radius-sm);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--js-transition);
}

.dialog-btn.cancel {
  background: transparent;
  border: 1px solid var(--js-card-border);
  color: var(--js-text-secondary);
}

.dialog-btn.cancel:hover {
  background: var(--js-page-bg);
}

.dialog-btn.primary {
  background: var(--js-primary);
  border: none;
  color: #fff;
}

.dialog-btn.primary:hover {
  background: var(--js-primary-light);
}

.dialog-btn.primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
