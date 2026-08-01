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
    <!-- 顶部操作栏 -->
    <div class="header">
      <h3>公司列表</h3>
      <el-button type="primary" :icon="Plus" @click="showAddDialog">
        添加公司
      </el-button>
    </div>

    <!-- 公司表格 -->
    <el-card>
      <el-table :data="companies" v-loading="loading" stripe>
        <el-table-column prop="name" label="公司名称" width="150" />
        <el-table-column prop="industry" label="行业" width="120" />
        <el-table-column prop="website" label="官网" min-width="200">
          <template #default="{ row }">
            <el-link
              v-if="row.website"
              :href="row.website"
              target="_blank"
              type="primary"
            >
              {{ row.website }}
            </el-link>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="career_page" label="招聘页" min-width="200">
          <template #default="{ row }">
            <el-link
              v-if="row.career_page"
              :href="row.career_page"
              target="_blank"
              type="primary"
            >
              {{ row.career_page }}
            </el-link>
            <span v-else>-</span>
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
              @click="disableCompany(row)"
            >
              禁用
            </el-button>
            <el-button
              v-else
              type="success"
              link
              @click="enableCompany(row)"
            >
              启用
            </el-button>
            <el-button
              type="danger"
              link
              :icon="Delete"
              @click="hardDeleteCompany(row)"
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
      :title="isEdit ? '编辑公司' : '添加公司'"
      width="600px"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="公司名称" prop="name">
          <el-input
            v-model="form.name"
            placeholder="请输入公司名称"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="公司别名">
          <el-select
            v-model="form.aliases"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="输入别名后回车添加"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="行业">
          <el-input
            v-model="form.industry"
            placeholder="如：互联网、人工智能、金融"
            maxlength="50"
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
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitForm">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.company-manage {
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
</style>
