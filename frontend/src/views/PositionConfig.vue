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
    <!-- 顶部操作栏 -->
    <div class="header">
      <h3>职位配置</h3>
      <el-button type="primary" :icon="Plus" @click="showAddDialog">
        添加职位
      </el-button>
    </div>

    <!-- 职位表格 -->
    <el-card>
      <el-table :data="positions" v-loading="loading" stripe>
        <el-table-column prop="title" label="职位名称" width="150" />
        <el-table-column label="搜索关键词" min-width="200">
          <template #default="{ row }">
            <el-tag
              v-for="keyword in row.keywords"
              :key="keyword"
              size="small"
              class="keyword-tag"
            >
              {{ keyword }}
            </el-tag>
            <span v-if="!row.keywords?.length">-</span>
          </template>
        </el-table-column>
        <el-table-column label="目标城市" min-width="150">
          <template #default="{ row }">
            <el-tag
              v-for="location in row.locations"
              :key="location"
              size="small"
              type="success"
              class="keyword-tag"
            >
              {{ location }}
            </el-tag>
            <span v-if="!row.locations?.length">全国</span>
          </template>
        </el-table-column>
        <el-table-column label="经验要求" width="100">
          <template #default="{ row }">
            {{ getExperienceLabel(row.experience_level) }}
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              :icon="Edit"
              @click="showEditDialog(row)"
            >
              编辑
            </el-button>
            <el-button
              v-if="row.is_active"
              type="warning"
              link
              @click="disablePosition(row)"
            >
              禁用
            </el-button>
            <el-button
              v-else
              type="success"
              link
              @click="enablePosition(row)"
            >
              启用
            </el-button>
            <el-button
              type="danger"
              link
              :icon="Delete"
              @click="hardDeletePosition(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑职位配置' : '添加职位配置'"
      width="600px"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="110px"
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
          />
          <div class="form-tip">
            用于搜索的关键词，如：Python、机器学习、大模型
          </div>
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
          />
          <div class="form-tip">
            包含这些关键词的结果将被过滤
          </div>
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
          />
          <div class="form-tip">
            不填则搜索全国范围
          </div>
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
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitForm">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.position-config {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.keyword-tag {
  margin-right: 6px;
  margin-bottom: 4px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
