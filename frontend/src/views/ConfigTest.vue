<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Check, Message, Refresh } from '@element-plus/icons-vue'
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

const emailConfig = ref<EmailConfigStatus | null>(null)
const emailConfigLoading = ref(false)
const emailTestLoading = ref(false)
const testRecipients = ref('')
const emailTestResult = ref<ConfigTestResult | null>(null)

const emailConfigLabel = computed(() => {
  if (!emailConfig.value) return '未检测'
  return emailConfig.value.configured ? 'SMTP 已配置' : 'SMTP 未完整配置'
})

const defaultRecipientLabel = computed(() => {
  const count = emailConfig.value?.recipient_count ?? 0
  return count > 0 ? `默认收件人 ${count} 个` : '未配置默认收件人'
})

const canTestEmail = computed(() => Boolean(emailConfig.value?.configured))

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

onMounted(() => {
  fetchEmailConfig()
})
</script>

<template>
  <div class="config-test">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2 class="page-title">配置可用性测试</h2>
      <p class="page-desc">检查外部服务配置是否可用，当前支持邮件发送测试</p>
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

    <!-- 待接入服务 -->
    <div class="test-card">
      <div class="card-header">
        <div class="card-title-wrap">
          <div class="card-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
            </svg>
          </div>
          <div>
            <h3 class="card-title">待接入服务</h3>
            <p class="card-desc">以下服务的连通性测试将在后续版本中添加</p>
          </div>
        </div>
      </div>
      <div class="card-body">
        <div class="pending-list">
          <div class="pending-item">
            <span class="status-dot pending"></span>
            <span class="service-name">模型 API</span>
            <span class="service-state pending">待接入</span>
          </div>
          <div class="pending-desc">后续接入 LLM Provider、Base URL、API Key 和模型连通性测试</div>

          <div class="pending-item">
            <span class="status-dot pending"></span>
            <span class="service-name">搜索 API</span>
            <span class="service-state pending">待接入</span>
          </div>
          <div class="pending-desc">后续接入 SerpAPI 等搜索服务的密钥校验</div>
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

/* ── 待接入列表 ── */
.pending-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.pending-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: #fafbfc;
  border: 1px solid var(--js-card-border);
  border-radius: var(--js-radius-md);
}

.pending-desc {
  font-size: 12px;
  color: var(--js-text-tertiary);
  padding: 0 16px 12px 16px;
  margin-top: -4px;
}
</style>