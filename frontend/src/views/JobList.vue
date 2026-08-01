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

    // 添加筛选条件
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
    <!-- 筛选条件 -->
    <el-card class="filter-card">
      <el-form :model="filters" inline>
        <el-form-item label="公司">
          <el-select
            v-model="filters.company_id"
            clearable
            placeholder="选择公司"
            style="width: 150px"
          >
            <el-option
              v-for="company in companies"
              :key="company.id"
              :label="company.name"
              :value="company.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="职位">
          <el-input
            v-model="filters.keyword"
            placeholder="搜索职位"
            clearable
            style="width: 150px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>

        <el-form-item label="地点">
          <el-input
            v-model="filters.location"
            placeholder="工作地点"
            clearable
            style="width: 120px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>

        <el-form-item label="薪资">
          <el-select
            placeholder="选择薪资范围"
            style="width: 120px"
            @change="handleSalaryChange"
          >
            <el-option
              v-for="(range, index) in salaryRanges"
              :key="index"
              :label="range.label"
              :value="range"
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

    <!-- 招聘信息表格 -->
    <el-card>
      <template #header>
        <div class="table-header">
          <span>招聘信息</span>
          <el-button
            v-if="selectedJobs.length"
            type="danger"
            :icon="Delete"
            @click="batchDeleteJobs"
          >
            批量删除（{{ selectedJobs.length }}）
          </el-button>
        </div>
      </template>
      <el-table :data="jobs" v-loading="loading" stripe @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="50" />
        <el-table-column prop="company_name" label="公司" width="120" />
        <el-table-column prop="job_title" label="职位" min-width="150" />
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
            <el-tag
              :type="isOpenType(row.is_open)"
              size="small"
            >
              {{ isOpenText(row.is_open) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="source_platform" label="来源" width="100" />
        <el-table-column label="更新时间" width="110">
          <template #default="{ row }">
            {{ formatDate(row.crawled_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="170" fixed="right">
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
              type="primary"
              link
              :icon="Link"
              @click="openSource(row)"
            >
              原文
            </el-button>
            <el-button
              type="danger"
              link
              :icon="Delete"
              @click="deleteJob(row)"
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
      title="职位详情"
      width="700px"
    >
      <div v-if="currentJob" class="job-detail">
        <h3>{{ currentJob.job_title }}</h3>

        <el-descriptions :column="2" border>
          <el-descriptions-item label="公司">
            {{ currentJob.company_name }}
          </el-descriptions-item>
          <el-descriptions-item label="薪资">
            {{ formatSalary(currentJob) }}
          </el-descriptions-item>
          <el-descriptions-item label="地点">
            {{ currentJob.location || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="经验">
            {{ currentJob.experience_years || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="学历">
            {{ currentJob.education || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="来源">
            {{ currentJob.source_platform || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="是否在招">
            <el-tag :type="isOpenType(currentJob.is_open)" size="small">
              {{ isOpenText(currentJob.is_open) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="原文链接" :span="2">
            <el-link
              v-if="currentJob.source_url"
              :href="currentJob.source_url"
              type="primary"
              target="_blank"
            >
              {{ currentJob.source_url }}
            </el-link>
            <span v-else>-</span>
          </el-descriptions-item>
          <el-descriptions-item label="发布时间" :span="2">
            {{ formatDate(currentJob.published_at) }}
          </el-descriptions-item>
        </el-descriptions>

        <div v-if="currentJob.skills?.length" class="section">
          <h4>技能要求 <span class="hint">（从搜索摘要提取，可能不完整）</span></h4>
          <div class="skills">
            <el-tag
              v-for="skill in currentJob.skills"
              :key="skill"
              class="skill-tag"
            >
              {{ skill }}
            </el-tag>
          </div>
        </div>

        <div v-if="currentJob.job_description" class="section">
          <h4>职位描述</h4>
          <div class="description">{{ currentJob.job_description }}</div>
        </div>

        <div v-if="currentJob.requirements" class="section">
          <h4>任职要求</h4>
          <div class="description">{{ currentJob.requirements }}</div>
        </div>

        <div v-if="currentJob.benefits?.length" class="section">
          <h4>福利待遇</h4>
          <div class="benefits">
            <el-tag
              v-for="benefit in currentJob.benefits"
              :key="benefit"
              type="success"
              class="benefit-tag"
            >
              {{ benefit }}
            </el-tag>
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button type="primary" @click="openSource(currentJob)">
          查看原文
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.job-list {
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

.salary {
  color: #e6a23c;
  font-weight: 600;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.job-detail h3 {
  margin: 0 0 20px 0;
  font-size: 20px;
  color: #303133;
}

.section {
  margin-top: 20px;
}

.section h4 {
  margin: 0 0 10px 0;
  font-size: 16px;
  color: #303133;
}

.hint {
  font-size: 12px;
  color: #999;
  font-weight: normal;
}

.skills,
.benefits {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.skill-tag,
.benefit-tag {
  margin: 0;
}

.description {
  white-space: pre-wrap;
  line-height: 1.8;
  color: #606266;
  background-color: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
}
</style>
