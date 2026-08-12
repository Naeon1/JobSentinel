<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Message, Refresh, VideoCamera, Search } from '@element-plus/icons-vue'
import { configTestApi } from '../api'

interface EmailConfigStatus {
  configured: boolean
  smtp_host: string
  smtp_port: number
  smtp_username?: string | null
  email_from?: string | null
  recipient_count: number
}

interface ConfigTestResult {
  type: 'success' | 'error' | 'warning'
  title: string
  message: string
}

interface LlmInfo {
  provider: string
  api_base_url: string
  model_name: string
  use_anthropic_format: boolean
  api_key_set: boolean
}

interface LlmTestState {
  status: 'idle' | 'loading' | 'success' | 'error'
  llm_info?: LlmInfo | null
  response?: string | null
  error?: string | null
}

interface SerpapiInfo {
  provider: string
  api_key_set: boolean
  engine: string
}

interface SerpapiTestState {
  status: 'idle' | 'loading' | 'success' | 'skipped' | 'error'
  api_info?: SerpapiInfo | null
  results_count?: number
  sample?: Array<{ title: string; link: string; snippet: string }> | null
  error?: string | null
}

const emailConfig = ref<EmailConfigStatus | null>(null)
const emailConfigLoading = ref(false)
const emailTestLoading = ref(false)
const testRecipients = ref('')
const emailTestResult = ref<ConfigTestResult | null>(null)

const llmTest = ref<LlmTestState>({ status: 'idle' })
const serpapiTest = ref<SerpapiTestState>({ status: 'idle' })

const emailConfigLabel = computed(() => {
  if (!emailConfig.value) return '未检测'
  return emailConfig.value.configured ? 'SMTP 已配置' : 'SMTP 未完整配置'
})

const defaultRecipientLabel = computed(() => {
  const count = emailConfig.value?.recipient_count ?? 0
  return count > 0 ? `默认收件人 ${count} 个` : '未配置默认收件人'
})

const canTestEmail = computed(() => Boolean(emailConfig.value?.configured))

// 模型 API 状态：已配置 key 才视为可用
const llmConfigured = computed(() => Boolean(llmTest.value.llm_info?.api_key_set))
const llmStatusLabel = computed(() => {
  if (llmTest.value.status === 'loading') return '检测中…'
  if (!llmTest.value.llm_info) return '未检测'
  return llmConfigured.value ? '已配置 API Key' : '未配置 API Key'
})

// 搜索 API 状态：已配置 key 才视为可用
const serpapiConfigured = computed(() => Boolean(serpapiTest.value.api_info?.api_key_set))
const serpapiStatusLabel = computed(() => {
  if (serpapiTest.value.status === 'loading') return '检测中…'
  if (!serpapiTest.value.api_info) return '未检测'
  return serpapiConfigured.value ? '已配置 SerpAPI Key' : '未配置 SerpAPI Key'
})

const parseTestRecipients = () => (
  testRecipients.value
    .split(/[\s,;，；]+/)
    .map((item) => item.trim())
    .filter(Boolean)
)

const fetchEmailConfig = async () => {
  emailConfigLoading.value = true
  try {
    emailConfig.value = await configTestApi.getEmailConfig() as unknown as EmailConfigStatus
  } catch (error) {
    console.error('获取邮件配置状态失败:', error)
  } finally {
    emailConfigLoading.value = false
  }
}

const sendTestEmail = async () => {
  emailTestLoading.value = true
  emailTestResult.value = null
  try {
    const recipients = parseTestRecipients()
    const data = await configTestApi.sendTestEmail({
      recipients: recipients.length > 0 ? recipients : undefined,
    }) as any

    emailTestResult.value = {
      type: 'success',
      title: '邮件发送成功',
      message: data.message || '测试邮件已提交发送',
    }
    ElMessage.success('测试邮件已发送')
    await fetchEmailConfig()
  } catch (error: any) {
    const message = error.response?.data?.detail || error.message || '测试邮件发送失败'
    emailTestResult.value = {
      type: 'error',
      title: '邮件发送失败',
      message,
    }
  } finally {
    emailTestLoading.value = false
  }
}

// 模型 API 连通性测试
const testLlm = async () => {
  llmTest.value = { status: 'loading' }
  try {
    const data = await configTestApi.testLlm() as any
    llmTest.value = {
      status: data.status === 'success' ? 'success' : 'error',
      llm_info: data.llm_info || null,
      response: data.response || null,
      error: data.error || null,
    }
    if (data.status === 'success') {
      ElMessage.success('模型 API 连通正常')
    } else {
      ElMessage.error('模型 API 测试失败')
    }
  } catch (error: any) {
    // test-llm 失败时仍会返回 200 + status:error，不会进这里；仅为兜底
    llmTest.value = {
      status: 'error',
      error: error.response?.data?.detail || error.message || '请求失败',
    }
    ElMessage.error('模型 API 请求失败')
  }
}

// 搜索 API（SerpAPI）连通性测试
const testSerpapi = async () => {
  serpapiTest.value = { status: 'loading' }
  try {
    const data = await configTestApi.testSerpapi() as any
    serpapiTest.value = {
      status: data.status || 'error',
      api_info: data.api_info || null,
      results_count: data.results_count ?? 0,
      sample: data.sample || null,
      error: data.error || null,
    }
    if (data.status === 'success') {
      ElMessage.success('搜索 API 连通正常')
    } else if (data.status === 'skipped') {
      ElMessage.warning('未配置 SerpAPI Key')
    } else {
      ElMessage.error('搜索 API 测试失败')
    }
  } catch (error: any) {
    serpapiTest.value = {
      status: 'error',
      error: error.response?.data?.detail || error.message || '请求失败',
    }
    ElMessage.error('搜索 API 请求失败')
  }
}

onMounted(() => {
  fetchEmailConfig()
})
</script>

<template>
  <div class="config-test">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2 class="page-title">配置可用性测试</h2>
      <p class="page-desc">检查外部服务配置是否可用：邮件发送、模型 API、搜索 API</p>
    </div>

    <!-- 邮件发送测试 -->
    <div class="test-card" v-loading="emailConfigLoading">
      <div class="card-header">
        <div class="card-title-wrap">
          <div class="card-icon">
            <el-icon :size="20"><Message /></el-icon>
          </div>
          <div>
            <h3 class="card-title">邮件发送</h3>
            <p class="card-desc">检查 SMTP 配置是否可用，发送测试邮件验证</p>
          </div>
        </div>
      </div>

      <div class="card-body">
        <div class="service-info">
          <div class="info-row">
            <span
              class="status-dot"
              :class="{ ok: emailConfig?.configured, fail: emailConfig && !emailConfig.configured }"
            ></span>
            <span class="service-name">邮件服务状态</span>
            <span
              class="service-state"
              :class="{ ok: emailConfig?.configured, fail: emailConfig && !emailConfig.configured }"
            >
              {{ emailConfigLabel }}
            </span>
            <button
              type="button"
              class="icon-btn"
              title="刷新邮件配置状态"
              @click="fetchEmailConfig"
              :disabled="emailConfigLoading"
            >
              <el-icon :size="16"><Refresh /></el-icon>
            </button>
          </div>
          <div class="meta-rows">
            <span>SMTP：{{ emailConfig?.smtp_host || '—' }}:{{ emailConfig?.smtp_port || '—' }}</span>
            <span>账号：{{ emailConfig?.smtp_username || '—' }}</span>
            <span>发件人：{{ emailConfig?.email_from || emailConfig?.smtp_username || '—' }}</span>
            <span>{{ defaultRecipientLabel }}</span>
          </div>
        </div>

        <div class="test-panel">
          <el-form label-position="top">
            <el-form-item label="测试收件人">
              <el-input
                v-model="testRecipients"
                type="textarea"
                :rows="2"
                placeholder="留空使用默认收件人，多个邮箱可用逗号、分号或换行分隔"
              />
              <div class="input-tip">
                如果默认收件人未配置，请在这里填入临时收件人。
              </div>
            </el-form-item>
          </el-form>

          <div class="form-actions">
            <button
              type="button"
              class="test-btn"
              @click="sendTestEmail"
              :disabled="!canTestEmail || emailTestLoading"
            >
              <el-icon :size="16"><Message /></el-icon>
              {{ emailTestLoading ? '发送中...' : '发送测试邮件' }}
            </button>
            <button
              type="button"
              class="secondary-btn"
              @click="fetchEmailConfig"
              :disabled="emailConfigLoading"
            >
              <el-icon :size="16"><Refresh /></el-icon>
              刷新状态
            </button>
          </div>

          <el-alert
            v-if="emailTestResult"
            class="test-result"
            :type="emailTestResult.type"
            :title="emailTestResult.title"
            :description="emailTestResult.message"
            show-icon
            :closable="false"
          />
        </div>
      </div>
    </div>

    <!-- 模型 API 测试 -->
    <div class="test-card">
      <div class="card-header">
        <div class="card-title-wrap">
          <div class="card-icon">
            <el-icon :size="20"><VideoCamera /></el-icon>
          </div>
          <div>
            <h3 class="card-title">模型 API</h3>
            <p class="card-desc">校验 LLM Provider、Base URL、API Key 配置并进行一次实际连通调用</p>
          </div>
        </div>
      </div>

      <div class="card-body">
        <div class="service-info">
          <div class="info-row">
            <span
              class="status-dot"
              :class="{
                ok: llmTest.status === 'success',
                fail: llmTest.status === 'error' || (llmTest.llm_info && !llmConfigured),
                pending: llmTest.status === 'loading' || !llmTest.llm_info,
              }"
            ></span>
            <span class="service-name">模型服务状态</span>
            <span
              class="service-state"
              :class="{
                ok: llmTest.status === 'success',
                fail: llmTest.status === 'error' || (llmTest.llm_info && !llmConfigured),
                pending: llmTest.status === 'loading' || !llmTest.llm_info,
              }"
            >
              {{ llmStatusLabel }}
            </span>
            <button
              type="button"
              class="icon-btn"
              title="刷新模型配置"
              @click="testLlm"
              :disabled="llmTest.status === 'loading'"
            >
              <el-icon :size="16"><Refresh /></el-icon>
            </button>
          </div>
          <div class="meta-rows">
            <span>Provider：{{ llmTest.llm_info?.provider || '—' }}</span>
            <span>Base URL：{{ llmTest.llm_info?.api_base_url || '—' }}</span>
            <span>模型：{{ llmTest.llm_info?.model_name || '—' }}</span>
            <span>API Key：{{ llmTest.llm_info?.api_key_set ? '已配置' : '—' }}</span>
          </div>
        </div>

        <div class="test-panel">
          <div class="input-tip" style="margin-top:0;margin-bottom:4px">
            点击下方按钮向 LLM 发送一次最小请求（"你好，请回复'连接成功'"），验证配置与连通性。
          </div>
          <div class="form-actions">
            <button
              type="button"
              class="test-btn"
              @click="testLlm"
              :disabled="llmTest.status === 'loading'"
            >
              <el-icon :size="16"><VideoCamera /></el-icon>
              {{ llmTest.status === 'loading' ? '测试中...' : '测试模型 API' }}
            </button>
          </div>

          <el-alert
            v-if="llmTest.status === 'success'"
            class="test-result"
            type="success"
            title="模型 API 连通正常"
            :description="llmTest.response ? `模型回复：${llmTest.response}` : 'LLM 已成功响应'"
            show-icon
            :closable="false"
          />
          <el-alert
            v-else-if="llmTest.status === 'error'"
            class="test-result"
            type="error"
            title="模型 API 测试失败"
            :description="llmTest.error || '请检查 LLM_API_KEY / LLM_API_BASE_URL / LLM_MODEL_NAME 配置'"
            show-icon
            :closable="false"
          />
        </div>
      </div>
    </div>

    <!-- 搜索 API 测试 -->
    <div class="test-card">
      <div class="card-header">
        <div class="card-title-wrap">
          <div class="card-icon">
            <el-icon :size="20"><Search /></el-icon>
          </div>
          <div>
            <h3 class="card-title">搜索 API</h3>
            <p class="card-desc">校验 SerpAPI Key 是否配置有效，进行一次最小搜索查询连通验证</p>
          </div>
        </div>
      </div>

      <div class="card-body">
        <div class="service-info">
          <div class="info-row">
            <span
              class="status-dot"
              :class="{
                ok: serpapiTest.status === 'success',
                fail: serpapiTest.status === 'error' || (serpapiTest.api_info && !serpapiConfigured),
                pending: serpapiTest.status === 'loading' || !serpapiTest.api_info,
              }"
            ></span>
            <span class="service-name">搜索服务状态</span>
            <span
              class="service-state"
              :class="{
                ok: serpapiTest.status === 'success',
                fail: serpapiTest.status === 'error' || (serpapiTest.api_info && !serpapiConfigured),
                pending: serpapiTest.status === 'loading' || !serpapiTest.api_info,
              }"
            >
              {{ serpapiStatusLabel }}
            </span>
            <button
              type="button"
              class="icon-btn"
              title="刷新搜索配置"
              @click="testSerpapi"
              :disabled="serpapiTest.status === 'loading'"
            >
              <el-icon :size="16"><Refresh /></el-icon>
            </button>
          </div>
          <div class="meta-rows">
            <span>服务商：{{ serpapiTest.api_info?.provider || '—' }}</span>
            <span>引擎：{{ serpapiTest.api_info?.engine || '—' }}</span>
            <span>API Key：{{ serpapiTest.api_info?.api_key_set ? '已配置' : '—' }}</span>
            <span v-if="serpapiTest.status === 'success'">命中：{{ serpapiTest.results_count ?? 0 }} 条</span>
          </div>
        </div>

        <div class="test-panel">
          <div class="input-tip" style="margin-top:0;margin-bottom:4px">
            点击下方按钮执行一次最小查询（仅 1 条结果），验证 SerpAPI Key 是否有效。不调用 LLM、不写数据库。
          </div>
          <div class="form-actions">
            <button
              type="button"
              class="test-btn"
              @click="testSerpapi"
              :disabled="serpapiTest.status === 'loading'"
            >
              <el-icon :size="16"><Search /></el-icon>
              {{ serpapiTest.status === 'loading' ? '测试中...' : '测试搜索 API' }}
            </button>
          </div>

          <el-alert
            v-if="serpapiTest.status === 'success'"
            class="test-result"
            type="success"
            title="搜索 API 连通正常"
            :description="serpapiTest.sample && serpapiTest.sample.length > 0 ? `样例结果：${serpapiTest.sample[0].title}` : 'SerpAPI 已成功返回结果'"
            show-icon
            :closable="false"
          />
          <el-alert
            v-else-if="serpapiTest.status === 'skipped'"
            class="test-result"
            type="warning"
            title="未配置 SerpAPI Key"
            :description="serpapiTest.error || '请在 .env 中设置 SERPAPI_KEY'"
            show-icon
            :closable="false"
          />
          <el-alert
            v-else-if="serpapiTest.status === 'error'"
            class="test-result"
            type="error"
            title="搜索 API 测试失败"
            :description="serpapiTest.error || '请检查 SERPAPI_KEY 是否正确或是否已耗尽免费额度'"
            show-icon
            :closable="false"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.config-test {
  max-width: 800px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* ── 页面标题 ── */
.page-header {
  margin-bottom: 8px;
}

.page-title {
  margin: 0 0 4px 0;
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

/* ── 测试卡片 ── */
.test-card {
  background: var(--js-card-bg);
  border: 1px solid var(--js-card-border);
  border-radius: var(--js-radius-lg);
  overflow: hidden;
  box-shadow: var(--js-card-shadow);
}

.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--js-card-border);
  background: #fafbfc;
}

.card-title-wrap {
  display: flex;
  gap: 12px;
}

.card-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--js-radius-md);
  background: var(--js-primary-alpha);
  color: var(--js-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.card-title {
  margin: 0 0 2px 0;
  font-size: 15px;
  font-weight: 700;
  color: var(--js-text-primary);
}

.card-desc {
  margin: 0;
  font-size: 13px;
  color: var(--js-text-tertiary);
}

.card-body {
  padding: 24px;
}

/* ── 服务信息 ── */
.service-info {
  padding: 16px;
  background: #f8fafc;
  border: 1px solid var(--js-card-border);
  border-radius: var(--js-radius-md);
  margin-bottom: 20px;
}

.info-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 24px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--js-text-tertiary);
  flex-shrink: 0;
}

.status-dot.ok {
  background: var(--js-success);
}

.status-dot.fail {
  background: var(--js-danger);
}

.status-dot.pending {
  background: var(--js-warning);
}

.service-name {
  font-size: 14px;
  font-weight: 700;
  color: var(--js-text-primary);
}

.service-state {
  padding: 2px 8px;
  border-radius: 999px;
  background: #e2e8f0;
  color: var(--js-text-secondary);
  font-size: 12px;
  font-weight: 700;
  line-height: 18px;
}

.service-state.ok {
  background: rgba(16, 185, 129, 0.12);
  color: #047857;
}

.service-state.fail {
  background: rgba(239, 68, 68, 0.12);
  color: #b91c1c;
}

.service-state.pending {
  background: rgba(245, 158, 11, 0.14);
  color: #b45309;
}

.meta-rows {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 16px;
  margin-top: 8px;
  font-size: 12px;
  color: var(--js-text-secondary);
  line-height: 1.6;
}

.icon-btn {
  width: 32px;
  height: 32px;
  border: 1px solid var(--js-card-border);
  border-radius: var(--js-radius-sm);
  background: #fff;
  color: var(--js-text-secondary);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all var(--js-transition);
  flex-shrink: 0;
  margin-left: auto;
}

.icon-btn:hover {
  border-color: var(--js-primary);
  color: var(--js-primary);
}

.icon-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ── 测试面板 ── */
.test-panel {
  padding: 20px;
  border: 1px solid var(--js-card-border);
  border-radius: var(--js-radius-md);
  background: #fff;
}

.input-tip {
  margin-top: 8px;
  font-size: 12px;
  color: var(--js-text-tertiary);
  line-height: 1.5;
}

.form-actions {
  margin-top: 16px;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.test-btn,
.secondary-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 9px 18px;
  border-radius: var(--js-radius-sm);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--js-transition);
}

.test-btn {
  background: var(--js-primary);
  color: #fff;
  border: 1px solid var(--js-primary);
}

.test-btn:hover {
  background: var(--js-primary-light);
  border-color: var(--js-primary-light);
}

.secondary-btn {
  background: #fff;
  color: var(--js-text-secondary);
  border: 1px solid var(--js-card-border);
}

.secondary-btn:hover {
  border-color: var(--js-primary);
  color: var(--js-primary);
}

.test-btn:disabled,
.secondary-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.test-result {
  margin-top: 16px;
}
</style>