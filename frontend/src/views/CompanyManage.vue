<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { Plus, Edit, Delete } from '@element-plus/icons-vue'
import { companyApi } from '../api'

// 数据
const companies = ref<any[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref<FormInstance>()

// 表单数据
const form = ref({
  id: '',
  name: '',
  aliases: [] as string[],
  industry: '',
  website: '',
  career_page: '',
  notes: '',
})

// 表单验证规则
const rules: FormRules = {
  name: [
    { required: true, message: '请输入公司名称', trigger: 'blur' },
    { min: 1, max: 100, message: '长度在 1 到 100 个字符', trigger: 'blur' },
  ],
  website: [
    { type: 'url', message: '请输入正确的URL', trigger: 'blur' },
  ],
  career_page: [
    { type: 'url', message: '请输入正确的URL', trigger: 'blur' },
  ],
}

// 获取公司列表
const fetchCompanies = async () => {
  loading.value = true
  try {
    const data = await companyApi.list() as any
    companies.value = data.items || []
  } catch (error) {
    console.error('获取公司列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 显示添加对话框
const showAddDialog = () => {
  isEdit.value = false
  form.value = {
    id: '',
    name: '',
    aliases: [],
    industry: '',
    website: '',
    career_page: '',
    notes: '',
  }
  dialogVisible.value = true
}

// 显示编辑对话框
const showEditDialog = (row: any) => {
  isEdit.value = true
  form.value = {
    id: row.id,
    name: row.name,
    aliases: row.aliases || [],
    industry: row.industry || '',
    website: row.website || '',
    career_page: row.career_page || '',
    notes: row.notes || '',
  }
  dialogVisible.value = true
}

// 提交表单
const submitForm = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      const { id, ...data } = form.value

      if (isEdit.value) {
        await companyApi.update(id, data)
        ElMessage.success('更新成功')
      } else {
        await companyApi.create(data)
        ElMessage.success('添加成功')
      }

      dialogVisible.value = false
      fetchCompanies()
    } catch (error) {
      console.error('提交失败:', error)
    } finally {
      submitting.value = false
    }
  })
}

// 禁用公司
const disableCompany = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要禁用公司"${row.name}"吗？`,
      '提示',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    await companyApi.delete(row.id)
    ElMessage.success('已禁用')
    fetchCompanies()
  } catch (error) {
    // 用户取消
  }
}

// 启用公司
const enableCompany = async (row: any) => {
  try {
    await companyApi.enable(row.id)
    ElMessage.success('已启用')
    fetchCompanies()
  } catch (error) {
    console.error('启用失败:', error)
  }
}

// 彻底删除公司
const hardDeleteCompany = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要彻底删除公司"${row.name}"吗？此操作不可恢复！`,
      '警告',
      { confirmButtonText: '彻底删除', cancelButtonText: '取消', type: 'error' }
    )
    await companyApi.hardDelete(row.id)
    ElMessage.success('已彻底删除')
    fetchCompanies()
  } catch (error) {
    // 用户取消
  }
}

onMounted(fetchCompanies)
</script>

<template>
  <div class="company-manage">
    <!-- 页面标题栏 -->
    <div class="page-header">
      <div class="header-info">
        <h2 class="page-title">公司管理</h2>
        <p class="page-desc">维护你的目标公司监测清单</p>
      </div>
      <button class="add-btn" @click="showAddDialog">
        <el-icon :size="16"><Plus /></el-icon>
        <span>添加公司</span>
      </button>
    </div>

    <!-- 公司表格 -->
    <div class="table-card">
      <el-table :data="companies" v-loading="loading" stripe>
        <el-table-column prop="name" label="公司名称" width="160">
          <template #default="{ row }">
            <div class="company-name">
              <div class="company-avatar">{{ row.name.charAt(0).toUpperCase() }}</div>
              <span>{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="industry" label="行业" width="120">
          <template #default="{ row }">
            <span v-if="row.industry" class="industry-tag">{{ row.industry }}</span>
            <span v-else class="text-tertiary">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="website" label="官网" min-width="200">
          <template #default="{ row }">
            <a
              v-if="row.website"
              :href="row.website"
              target="_blank"
              class="link"
            >
              {{ row.website }}
            </a>
            <span v-else class="text-tertiary">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="career_page" label="招聘页" min-width="200">
          <template #default="{ row }">
            <a
              v-if="row.career_page"
              :href="row.career_page"
              target="_blank"
              class="link"
            >
              {{ row.career_page }}
            </a>
            <span v-else class="text-tertiary">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="90">
          <template #default="{ row }">
            <div class="status-wrap">
              <span class="status-dot" :class="row.is_active ? 'active' : 'inactive'"></span>
              <span>{{ row.is_active ? '启用' : '禁用' }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <div class="action-btns">
              <button class="action-btn" @click="showEditDialog(row)">
                <el-icon :size="14"><Edit /></el-icon>
              </button>
              <button
                v-if="row.is_active"
                class="action-btn warning"
                @click="disableCompany(row)"
              >
                <span class="btn-text">禁用</span>
              </button>
              <button
                v-else
                class="action-btn success"
                @click="enableCompany(row)"
              >
                <span class="btn-text">启用</span>
              </button>
              <button
                class="action-btn danger"
                @click="hardDeleteCompany(row)"
              >
                <el-icon :size="14"><Delete /></el-icon>
              </button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <el-empty
        v-if="!loading && !companies.length"
        description="暂无公司，点击上方按钮添加"
        :image-size="80"
        style="padding: 60px 0"
      />
    </div>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑公司' : '添加公司'"
      width="560px"
      destroy-on-close
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
      >
        <div class="form-row">
          <el-form-item label="公司名称" prop="name" class="form-item-full">
            <el-input
              v-model="form.name"
              placeholder="请输入公司名称"
              maxlength="100"
              show-word-limit
            />
          </el-form-item>
        </div>

        <div class="form-row two-col">
          <el-form-item label="行业" prop="industry" class="form-item-half">
            <el-input
              v-model="form.industry"
              placeholder="如：互联网、人工智能"
              maxlength="50"
            />
          </el-form-item>
        </div>

        <el-form-item label="公司别名">
          <el-select
            v-model="form.aliases"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="输入别名后回车添加"
            style="width: 100%"
            :persistent="false"
          />
        </el-form-item>

        <el-form-item label="公司官网" prop="website">
          <el-input
            v-model="form.website"
            placeholder="https://..."
          />
        </el-form-item>

        <el-form-item label="招聘页面" prop="career_page">
          <el-input
            v-model="form.career_page"
            placeholder="https://..."
          />
        </el-form-item>

        <el-form-item label="备注">
          <el-input
            v-model="form.notes"
            type="textarea"
            :rows="3"
            placeholder="可选备注信息"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <button class="dialog-btn cancel" @click="dialogVisible = false">取消</button>
        <button class="dialog-btn primary" @click="submitForm" :disabled="submitting">
          {{ submitting ? '保存中...' : '确定' }}
        </button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.company-manage {
  max-width: 1200px;
  margin: 0 auto;
}

/* ── 页面标题栏 ── */
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 24px;
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

.add-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 18px;
  background: var(--js-primary);
  color: #fff;
  border: none;
  border-radius: var(--js-radius-sm);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--js-transition);
}

.add-btn:hover {
  background: var(--js-primary-light);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

/* ── 表格卡片 ── */
.table-card {
  background: var(--js-card-bg);
  border: 1px solid var(--js-card-border);
  border-radius: var(--js-radius-lg);
  overflow: hidden;
  box-shadow: var(--js-card-shadow);
}

/* ── 公司名称单元格 ── */
.company-name {
  display: flex;
  align-items: center;
  gap: 10px;
}

.company-avatar {
  width: 32px;
  height: 32px;
  border-radius: var(--js-radius-sm);
  background: var(--js-primary-alpha);
  color: var(--js-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  flex-shrink: 0;
}

.industry-tag {
  display: inline-flex;
  padding: 2px 8px;
  background: #f1f5f9;
  color: var(--js-text-secondary);
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.link {
  color: var(--js-primary);
  text-decoration: none;
  transition: color var(--js-transition);
}

.link:hover {
  color: var(--js-primary-light);
  text-decoration: underline;
}

.text-tertiary {
  color: var(--js-text-tertiary);
}

/* ── 状态 ── */
.status-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--js-text-secondary);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot.active {
  background: var(--js-success);
  box-shadow: 0 0 6px var(--js-success);
}

.status-dot.inactive {
  background: var(--js-text-tertiary);
}

/* ── 操作按钮 ── */
.action-btns {
  display: flex;
  align-items: center;
  gap: 4px;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 5px 10px;
  border: none;
  background: transparent;
  border-radius: var(--js-radius-sm);
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  color: var(--js-text-secondary);
  transition: all var(--js-transition);
}

.action-btn:hover {
  background: var(--js-page-bg);
  color: var(--js-text-primary);
}

.action-btn.warning {
  color: var(--js-warning);
}

.action-btn.warning:hover {
  background: rgba(245, 158, 11, 0.1);
}

.action-btn.success {
  color: var(--js-success);
}

.action-btn.success:hover {
  background: rgba(16, 185, 129, 0.1);
}

.action-btn.danger:hover {
  background: rgba(239, 68, 68, 0.1);
  color: var(--js-danger);
}

.btn-text {
  font-size: 13px;
}

/* ── 对话框 ── */
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
  color: var(--js-text-primary);
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
  opacity: 0.6;
  cursor: not-allowed;
}

/* ── 表单 ── */
.form-row {
  display: flex;
  gap: 16px;
}

.form-item-full {
  flex: 1;
}

.form-item-half {
  flex: 1;
}
</style>
