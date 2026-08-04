<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { Check } from '@element-plus/icons-vue'
import { scheduleApi } from '../api'
import {
  type ScheduleConfig,
  defaultScheduleConfig,
  toCron,
  fromCron,
  describeConfig,
} from '../utils/cronUtils'

// 定时任务配置（含 is_enabled 与友好配置）
const scheduleConfig = ref<ScheduleConfig>(defaultScheduleConfig())
const scheduleEnabled = ref(true)
const scheduleFormRef = ref<FormInstance>()
const scheduleLoading = ref(false)

// 后端返回的下次执行时间（ISO），仅展示用
const nextRunAt = ref<string | null>(null)

// 是否展开高级模式（直接编辑 Cron）
const advancedMode = ref(false)

// 频率选项
const frequencyOptions = [
  { label: '每天定点', value: 'daily' },
  { label: '每隔 N 小时', value: 'every_n_hours' },
  { label: '工作日定点（周一至周五）', value: 'weekdays' },
  { label: '每周定点', value: 'weekly' },
  { label: '每隔 N 分钟', value: 'every_n_minutes' },
  { label: '高级（自定义 Cron）', value: 'custom' },
]

// 星期选项（0=周日 ... 6=周六）
const weekdayOptions = [
  { label: '周一', value: 1 },
  { label: '周二', value: 2 },
  { label: '周三', value: 3 },
  { label: '周四', value: 4 },
  { label: '周五', value: 5 },
  { label: '周六', value: 6 },
  { label: '周日', value: 0 },
]

// 实时计算的 Cron 表达式
const cronExpression = computed(() => toCron(scheduleConfig.value) ?? scheduleConfig.value.cron_expression)

// 中文描述
const humanDescription = computed(() => describeConfig(scheduleConfig.value))

// 下次执行时间的本地化展示
const nextRunText = computed(() => {
  if (!nextRunAt.value) return '—'
  try {
    const d = new Date(nextRunAt.value)
    const pad = (n: number) => String(n).padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
  } catch {
    return nextRunAt.value
  }
})

const isBrowserCST = computed(() => {
  try {
    return new Date().getTimezoneOffset() === -480
  } catch {
    return false
  }
})

const nextRunBeijingText = computed(() => {
  if (!nextRunAt.value) return '—'
  try {
    const d = new Date(nextRunAt.value)
    const pad = (n: number) => String(n).padStart(2, '0')
    const beijing = new Date(d.toLocaleString('en-US', { timeZone: 'Asia/Shanghai' }))
    return `${pad(beijing.getMonth() + 1)}-${pad(beijing.getDate())} ${pad(beijing.getHours())}:${pad(beijing.getMinutes())}`
  } catch {
    return '—'
  }
})

// 切到 custom 时自动展开高级模式
watch(
  () => scheduleConfig.value.frequency,
  (f) => {
    advancedMode.value = f === 'custom'
  }
)

// 表单验证规则
const scheduleRules: FormRules = {
  cron_expression: [
    { required: true, message: '请输入 Cron 表达式', trigger: 'blur' },
  ],
}

const cronHelp = `Cron 5个字段，空格分隔：分 时 日 月 周（按北京时间执行）
- 0 9 * * *    每天 9:00（北京）
- 0 */2 * * *  每 2 小时整点
- 0 9 * * 1-5  工作日 9:00
- 0 9,18 * * * 每天 9:00 和 18:00`

// 获取定时任务配置
const fetchScheduleConfig = async () => {
  scheduleLoading.value = true
  try {
    const data = await scheduleApi.getCurrent() as any
    scheduleEnabled.value = data.is_enabled ?? true
    nextRunAt.value = data.next_run_at ?? null
    if (data.cron_expression) {
      scheduleConfig.value = fromCron(data.cron_expression)
    }
  } catch (error) {
    console.error('获取定时任务配置失败:', error)
  } finally {
    scheduleLoading.value = false
  }
}

// 保存定时任务配置
const saveScheduleConfig = async () => {
  if (!scheduleFormRef.value) return

  await scheduleFormRef.value.validate(async (valid) => {
    if (!valid) return

    try {
      const data = await scheduleApi.updateCurrent({
        cron_expression: cronExpression.value,
        is_enabled: scheduleEnabled.value,
      }) as any
      nextRunAt.value = data.next_run_at ?? nextRunAt.value
      ElMessage.success(`定时任务配置已保存（${humanDescription.value}）`)
    } catch (error) {
      console.error('保存配置失败:', error)
    }
  })
}

onMounted(fetchScheduleConfig)
</script>

<template>
  <div class="settings">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2 class="page-title">系统设置</h2>
      <p class="page-desc">配置定时任务和系统参数</p>
    </div>

    <!-- 定时任务配置 -->
    <div class="settings-card" v-loading="scheduleLoading">
      <div class="card-header">
        <div class="card-title-wrap">
          <div class="card-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12 6 12 12 16 14"/>
            </svg>
          </div>
          <div>
            <h3 class="card-title">定时任务配置</h3>
            <p class="card-desc">设置自动执行搜索任务的时间和频率</p>
          </div>
        </div>
        <div class="enable-toggle">
          <span class="toggle-label" :class="{ active: scheduleEnabled }">
            {{ scheduleEnabled ? '已启用' : '已关闭' }}
          </span>
          <div
            class="toggle-switch"
            :class="{ on: scheduleEnabled }"
            @click="scheduleEnabled = !scheduleEnabled"
          >
            <div class="toggle-dot"></div>
          </div>
        </div>
      </div>

      <div class="card-body">
        <el-form
          ref="scheduleFormRef"
          :model="scheduleConfig"
          :rules="scheduleRules"
          label-position="top"
          :disabled="!scheduleEnabled"
        >
          <!-- 频率选择 -->
          <el-form-item label="执行频率" prop="frequency">
            <div class="frequency-grid">
              <button
                v-for="opt in frequencyOptions"
                :key="opt.value"
                type="button"
                class="freq-btn"
                :class="{ active: scheduleConfig.frequency === opt.value }"
                @click="scheduleConfig.frequency = opt.value as any"
              >
                {{ opt.label }}
              </button>
            </div>
          </el-form-item>

          <!-- 每天定点 -->
          <el-form-item v-if="scheduleConfig.frequency === 'daily'" label="执行时间">
            <div class="time-inputs">
              <el-time-select
                v-model="scheduleConfig.hour"
                start="00" step="01" end="23"
                placeholder="时" style="width: 110px"
              />
              <span class="time-sep">时</span>
              <el-time-select
                v-model="scheduleConfig.minute"
                start="00" step="05" end="55"
                placeholder="分" style="width: 110px"
              />
              <span class="time-sep">分</span>
            </div>
          </el-form-item>

          <!-- 每 N 小时 -->
          <el-form-item v-else-if="scheduleConfig.frequency === 'every_n_hours'" label="间隔小时">
            <div class="interval-input">
              <el-input-number
                v-model="scheduleConfig.interval"
                :min="1" :max="23" :step="1"
              />
              <span class="interval-text">小时执行一次</span>
            </div>
          </el-form-item>

          <!-- 工作日定点 -->
          <el-form-item v-else-if="scheduleConfig.frequency === 'weekdays'" label="执行时间">
            <div class="time-inputs">
              <el-time-select
                v-model="scheduleConfig.hour"
                start="00" step="01" end="23"
                placeholder="时" style="width: 110px"
              />
              <span class="time-sep">时</span>
              <el-time-select
                v-model="scheduleConfig.minute"
                start="00" step="05" end="55"
                placeholder="分" style="width: 110px"
              />
              <span class="time-sep time-label">（周一至周五）</span>
            </div>
          </el-form-item>

          <!-- 每周定点 -->
          <el-form-item v-else-if="scheduleConfig.frequency === 'weekly'" label="执行时间">
            <div class="weekday-inputs">
              <el-select v-model="scheduleConfig.weekday" style="width: 100px">
                <el-option
                  v-for="opt in weekdayOptions"
                  :key="opt.value"
                  :label="opt.label"
                  :value="opt.value"
                />
              </el-select>
              <el-time-select
                v-model="scheduleConfig.hour"
                start="00" step="01" end="23"
                placeholder="时" style="width: 110px"
              />
              <span class="time-sep">时</span>
              <el-time-select
                v-model="scheduleConfig.minute"
                start="00" step="05" end="55"
                placeholder="分" style="width: 110px"
              />
              <span class="time-sep">分</span>
            </div>
          </el-form-item>

          <!-- 每 N 分钟 -->
          <el-form-item v-else-if="scheduleConfig.frequency === 'every_n_minutes'" label="间隔分钟">
            <div class="interval-input">
              <el-input-number
                v-model="scheduleConfig.interval"
                :min="1" :max="59" :step="1"
              />
              <span class="interval-text">分钟执行一次</span>
            </div>
          </el-form-item>

          <!-- 高级：自定义 Cron -->
          <el-form-item v-else-if="scheduleConfig.frequency === 'custom'" label="Cron 表达式" prop="cron_expression">
            <el-input
              v-model="scheduleConfig.cron_expression"
              placeholder="0 9 * * *"
              style="width: 240px"
            />
            <pre class="cron-help">{{ cronHelp }}</pre>
          </el-form-item>

          <!-- 时区提示 -->
          <div class="tz-hint">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>
            </svg>
            所有执行时间均按<strong>北京时间（UTC+8）</strong>计算
          </div>

          <!-- 实际生效预览 -->
          <div class="preview-block" v-if="scheduleEnabled">
            <div class="preview-title">实际生效配置</div>
            <div class="preview-grid">
              <div class="preview-item">
                <span class="preview-label">Cron 表达式</span>
                <code class="preview-value">{{ cronExpression }}</code>
              </div>
              <div class="preview-item">
                <span class="preview-label">中文说明</span>
                <span class="preview-value">{{ humanDescription }}</span>
              </div>
              <div class="preview-item">
                <span class="preview-label">下次执行</span>
                <span class="preview-value highlight">{{ nextRunText }}</span>
                <span v-if="!isBrowserCST" class="preview-bj">（北京时间 {{ nextRunBeijingText }}）</span>
              </div>
            </div>
          </div>
          <div class="preview-block disabled" v-else>
            <span class="disabled-text">定时任务已关闭，开启上方开关即可启用</span>
          </div>

          <!-- 保存按钮 -->
          <div class="form-actions">
            <button
              type="button"
              class="save-btn"
              @click="saveScheduleConfig"
              :disabled="!scheduleEnabled"
            >
              <el-icon :size="16"><Check /></el-icon>
              保存配置
            </button>
          </div>
        </el-form>
      </div>
    </div>

    <!-- API密钥配置 -->
    <div class="settings-card">
      <div class="card-header">
        <div class="card-title-wrap">
          <div class="card-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
            </svg>
          </div>
          <div>
            <h3 class="card-title">API 密钥配置</h3>
            <p class="card-desc">配置外部服务访问凭证</p>
          </div>
        </div>
      </div>
      <div class="card-body">
        <div class="info-alert">
          <div class="alert-icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>
            </svg>
          </div>
          <div class="alert-content">
            <p>API 密钥需要在后端环境变量中配置（<code>.env</code> 文件）：</p>
            <ul>
              <li><code>ANTHROPIC_API_KEY</code> — Claude API 密钥</li>
              <li><code>SERPAPI_KEY</code> — SerpAPI 搜索密钥</li>
              <li><code>SMTP_*</code> — 邮件发送配置</li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <!-- 关于 -->
    <div class="settings-card">
      <div class="card-header">
        <div class="card-title-wrap">
          <div class="card-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>
            </svg>
          </div>
          <div>
            <h3 class="card-title">关于系统</h3>
            <p class="card-desc">系统信息和资源链接</p>
          </div>
        </div>
      </div>
      <div class="card-body">
        <div class="about-grid">
          <div class="about-item">
            <span class="about-label">系统名称</span>
            <span class="about-value">JobSentinel</span>
          </div>
          <div class="about-item">
            <span class="about-label">版本</span>
            <span class="about-value">1.0.0</span>
          </div>
          <div class="about-item">
            <span class="about-label">技术栈</span>
            <span class="about-value">Vue 3 + Element Plus + FastAPI + OpenAI SDK</span>
          </div>
          <div class="about-item full">
            <span class="about-label">功能说明</span>
            <span class="about-value">基于 AI 的招聘信息自动搜索和分析系统，支持定时任务、邮件通知等功能</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.settings {
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

/* ── 设置卡片 ── */
.settings-card {
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

/* ── 启用开关 ── */
.enable-toggle {
  display: flex;
  align-items: center;
  gap: 10px;
}

.toggle-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--js-text-tertiary);
  transition: color var(--js-transition);
}

.toggle-label.active {
  color: var(--js-success);
}

.toggle-switch {
  width: 44px;
  height: 24px;
  border-radius: 12px;
  background: #e2e8f0;
  cursor: pointer;
  position: relative;
  transition: all var(--js-transition);
}

.toggle-switch.on {
  background: var(--js-success);
}

.toggle-dot {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
  transition: all var(--js-transition);
}

.toggle-switch.on .toggle-dot {
  transform: translateX(20px);
}

/* ── 卡片内容 ── */
.card-body {
  padding: 24px;
}

/* ── 频率选择网格 ── */
.frequency-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

@media (max-width: 640px) {
  .frequency-grid { grid-template-columns: repeat(2, 1fr); }
}

.freq-btn {
  padding: 10px 16px;
  background: var(--js-card-bg);
  border: 1px solid var(--js-card-border);
  border-radius: var(--js-radius-sm);
  font-size: 13px;
  font-weight: 500;
  color: var(--js-text-secondary);
  cursor: pointer;
  transition: all var(--js-transition);
  text-align: center;
}

.freq-btn:hover {
  border-color: var(--js-primary);
  color: var(--js-primary);
}

.freq-btn.active {
  background: var(--js-primary-alpha);
  border-color: var(--js-primary);
  color: var(--js-primary);
  font-weight: 700;
}

/* ── 时间输入 ── */
.time-inputs,
.weekday-inputs {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.time-sep {
  color: var(--js-text-tertiary);
  font-size: 13px;
}

.time-label {
  font-size: 12px;
  color: var(--js-text-tertiary);
}

.interval-input {
  display: flex;
  align-items: center;
  gap: 10px;
}

.interval-text {
  font-size: 13px;
  color: var(--js-text-secondary);
}

/* ── Cron 帮助 ── */
.cron-help {
  margin: 10px 0 0 0;
  font-size: 12px;
  color: var(--js-text-tertiary);
  line-height: 1.8;
  white-space: pre-wrap;
  font-family: 'Cascadia Code', 'Fira Code', Consolas, monospace;
  background: #f8fafc;
  padding: 12px;
  border-radius: var(--js-radius-sm);
}

/* ── 时区提示 ── */
.tz-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 16px;
  font-size: 12px;
  color: var(--js-text-tertiary);
}

.tz-hint strong {
  color: var(--js-text-secondary);
}

/* ── 预览块 ── */
.preview-block {
  margin-top: 20px;
  padding: 16px;
  background: var(--js-page-bg);
  border-radius: var(--js-radius-md);
  border: 1px solid var(--js-card-border);
}

.preview-block.disabled {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60px;
}

.disabled-text {
  color: var(--js-text-tertiary);
  font-size: 13px;
}

.preview-title {
  font-size: 12px;
  font-weight: 700;
  color: var(--js-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: 12px;
}

.preview-grid {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.preview-item {
  display: flex;
  align-items: baseline;
  gap: 10px;
  font-size: 13px;
}

.preview-label {
  min-width: 70px;
  color: var(--js-text-tertiary);
  font-weight: 500;
  flex-shrink: 0;
}

.preview-value {
  color: var(--js-text-primary);
}

.preview-value.highlight {
  color: var(--js-primary);
  font-weight: 700;
  font-size: 14px;
}

code.preview-value {
  font-family: 'Cascadia Code', 'Fira Code', Consolas, monospace;
  background: var(--js-card-bg);
  padding: 2px 8px;
  border-radius: 4px;
  color: #f59e0b;
}

.preview-bj {
  font-size: 12px;
  color: var(--js-text-tertiary);
}

/* ── 保存按钮 ── */
.form-actions {
  margin-top: 24px;
}

.save-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 24px;
  background: var(--js-primary);
  color: #fff;
  border: none;
  border-radius: var(--js-radius-sm);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--js-transition);
}

.save-btn:hover {
  background: var(--js-primary-light);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.save-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

/* ── 信息提示 ── */
.info-alert {
  display: flex;
  gap: 12px;
  padding: 14px 16px;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: var(--js-radius-md);
}

.alert-icon {
  color: var(--js-primary);
  flex-shrink: 0;
  margin-top: 2px;
}

.alert-content {
  font-size: 13px;
  color: #1e40af;
  line-height: 1.6;
}

.alert-content p {
  margin: 0 0 6px 0;
}

.alert-content ul {
  margin: 0;
  padding-left: 20px;
}

.alert-content li {
  margin-bottom: 4px;
}

.alert-content code {
  background: rgba(59, 130, 246, 0.1);
  padding: 1px 5px;
  border-radius: 3px;
  font-family: 'Cascadia Code', 'Fira Code', Consolas, monospace;
}

/* ── 关于信息 ── */
.about-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

@media (max-width: 640px) {
  .about-grid { grid-template-columns: 1fr; }
}

.about-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.about-item.full {
  grid-column: 1 / -1;
}

.about-label {
  font-size: 12px;
  color: var(--js-text-tertiary);
  font-weight: 600;
}

.about-value {
  font-size: 14px;
  color: var(--js-text-primary);
  font-weight: 500;
}
</style>
