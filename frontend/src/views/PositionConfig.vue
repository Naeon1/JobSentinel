<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { Plus, Edit, Delete } from '@element-plus/icons-vue'
import { positionApi } from '../api'

// 数据
const positions = ref<any[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref<FormInstance>()

// 表单数据
const form = ref({
  id: '',
  title: '',
  keywords: [] as string[],
  exclude_keywords: [] as string[],
  locations: [] as string[],
  experience_level: '',
})

// 表单验证规则
const rules: FormRules = {
  title: [
    { required: true, message: '请输入职位名称', trigger: 'blur' },
    { min: 1, max: 100, message: '长度在 1 到 100 个字符', trigger: 'blur' },
  ],
}

// 经验等级选项
const experienceLevels = [
  { label: '不限', value: '' },
  { label: '应届生', value: 'fresh' },
  { label: '1-3年', value: 'junior' },
  { label: '3-5年', value: 'mid' },
  { label: '5-10年', value: 'senior' },
  { label: '10年以上', value: 'expert' },
]

// 获取职位配置列表
const fetchPositions = async () => {
  loading.value = true
  try {
    const data = await positionApi.list() as any
    positions.value = data.items || []
  } catch (error) {
    console.error('获取职位配置失败:', error)
  } finally {
    loading.value = false
  }
}

// 显示添加对话框
const showAddDialog = () => {
  isEdit.value = false
  form.value = {
    id: '',
    title: '',
    keywords: [],
    exclude_keywords: [],
    locations: [],
    experience_level: '',
  }
  dialogVisible.value = true
}

// 显示编辑对话框
const showEditDialog = (row: any) => {
  isEdit.value = true
  form.value = {
    id: row.id,
    title: row.title,
    keywords: row.keywords || [],
    exclude_keywords: row.exclude_keywords || [],
    locations: row.locations || [],
    experience_level: row.experience_level || '',
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
        await positionApi.update(id, data)
        ElMessage.success('更新成功')
      } else {
        await positionApi.create(data)
        ElMessage.success('添加成功')
      }

      dialogVisible.value = false
      fetchPositions()
    } catch (error) {
      console.error('提交失败:', error)
    } finally {
      submitting.value = false
    }
  })
}

// 禁用职位配置
const disablePosition = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要禁用职位"${row.title}"吗？`,
      '提示',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    await positionApi.delete(row.id)
    ElMessage.success('已禁用')
    fetchPositions()
  } catch (error) {
    // 用户取消
  }
}

// 启用职位配置
const enablePosition = async (row: any) => {
  try {
    await positionApi.enable(row.id)
    ElMessage.success('已启用')
    fetchPositions()
  } catch (error) {
    console.error('启用失败:', error)
  }
}

// 彻底删除职位配置
const hardDeletePosition = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要彻底删除职位"${row.title}"吗？此操作不可恢复！`,
      '警告',
      { confirmButtonText: '彻底删除', cancelButtonText: '取消', type: 'error' }
    )
    await positionApi.hardDelete(row.id)
    ElMessage.success('已彻底删除')
    fetchPositions()
  } catch (error) {
    // 用户取消
  }
}

// 获取经验等级标签
const getExperienceLabel = (level: string) => {
  const item = experienceLevels.find((l) => l.value === level)
  return item ? item.label : '不限'
}

onMounted(fetchPositions)
</script>

<template>
  <div class="position-config">
    <!-- 页面标题栏 -->
    <div class="page-header">
      <div class="header-info">
        <h2 class="page-title">职位配置</h2>
        <p class="page-desc">配置搜索关键词、排除词和目标城市</p>
      </div>
      <button class="add-btn" @click="showAddDialog">
        <el-icon :size="16"><Plus /></el-icon>
        <span>添加职位</span>
      </button>
    </div>

    <!-- 职位表格 -->
    <div class="table-card">
      <el-table :data="positions" v-loading="loading" stripe>
        <el-table-column prop="title" label="职位名称" width="160">
          <template #default="{ row }">
            <div class="position-title">
              <span>{{ row.title }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="搜索关键词" min-width="220">
          <template #default="{ row }">
            <div class="tags-wrap" v-if="row.keywords?.length">
              <span
                v-for="keyword in row.keywords"
                :key="keyword"
                class="tag keyword-tag"
              >
                {{ keyword }}
              </span>
            </div>
            <span v-else class="text-tertiary">-</span>
          </template>
        </el-table-column>
        <el-table-column label="目标城市" min-width="160">
          <template #default="{ row }">
            <div class="tags-wrap" v-if="row.locations?.length">
              <span
                v-for="location in row.locations"
                :key="location"
                class="tag location-tag"
              >
                {{ location }}
              </span>
            </div>
            <span v-else class="text-tertiary">全国</span>
          </template>
        </el-table-column>
        <el-table-column label="经验要求" width="100">
          <template #default="{ row }">
            <span class="experience-badge">{{ getExperienceLabel(row.experience_level) }}</span>
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
                @click="disablePosition(row)"
              >
                <span class="btn-text">禁用</span>
              </button>
              <button
                v-else
                class="action-btn success"
                @click="enablePosition(row)"
              >
                <span class="btn-text">启用</span>
              </button>
              <button
                class="action-btn danger"
                @click="hardDeletePosition(row)"
              >
                <el-icon :size="14"><Delete /></el-icon>
              </button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <el-empty
        v-if="!loading && !positions.length"
        description="暂无职位配置，点击上方按钮添加"
        :image-size="80"
        style="padding: 60px 0"
      />
    </div>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑职位配置' : '添加职位配置'"
      width="560px"
      destroy-on-close
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
      >
        <el-form-item label="职位名称" prop="title">
          <el-input
            v-model="form.title"
            placeholder="如：AI工程师、后端开发"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="搜索关键词">
          <el-select
            v-model="form.keywords"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="输入关键词后回车添加"
            style="width: 100%"
            :persistent="false"
          />
          <div class="form-tip">用于搜索的关键词，如：Python、机器学习、大模型</div>
        </el-form-item>

        <el-form-item label="排除关键词">
          <el-select
            v-model="form.exclude_keywords"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="输入要排除的关键词"
            style="width: 100%"
            :persistent="false"
          />
          <div class="form-tip">包含这些关键词的结果将被过滤</div>
        </el-form-item>

        <el-form-item label="目标城市">
          <el-select
            v-model="form.locations"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="输入城市后回车添加"
            style="width: 100%"
            :persistent="false"
          />
          <div class="form-tip">不填则搜索全国范围</div>
        </el-form-item>

        <el-form-item label="经验要求">
          <el-select
            v-model="form.experience_level"
            placeholder="选择经验要求"
            style="width: 100%"
          >
            <el-option
              v-for="item in experienceLevels"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
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
.position-config {
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

/* ── 职位标题 ── */
.position-title {
  font-weight: 600;
  color: var(--js-text-primary);
}

/* ── 标签 ── */
.tags-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.tag {
  display: inline-flex;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.keyword-tag {
  background: var(--js-primary-alpha);
  color: var(--js-primary);
}

.location-tag {
  background: rgba(16, 185, 129, 0.1);
  color: var(--js-success);
}

.experience-badge {
  display: inline-flex;
  padding: 2px 8px;
  background: #f1f5f9;
  color: var(--js-text-secondary);
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
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

/* ── 表单 ── */
.form-tip {
  font-size: 12px;
  color: var(--js-text-tertiary);
  margin-top: 4px;
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
</style>
