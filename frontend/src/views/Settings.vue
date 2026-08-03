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
    // 用本地时间友好展示
    const pad = (n: number) => String(n).padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
  } catch {
    return nextRunAt.value
  }
})

// 浏览器是否处于东八区（用于决定是否显示"北京时间"补充行）
const isBrowserCST = computed(() => {
  try {
    // getTimezoneOffset 返回的是 UTC - 本地，分钟；东八区为 -480
    return new Date().getTimezoneOffset() === -480
  } catch {
    return false
  }
})

// 下次执行时间对应的北京时间（无论浏览器在哪个时区都恒定，因后端按东八区触发）
const nextRunBeijingText = computed(() => {
  if (!nextRunAt.value) return '—'
  try {
    const d = new Date(nextRunAt.value)
    const pad = (n: number) => String(n).padStart(2, '0')
    // toLocaleString 指定时区 Asia/Shanghai，无论浏览器本地时区如何都输出北京时间
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

// 表单验证规则（仅在高级模式校验 Cron 格式）
const scheduleRules: FormRules = {
  cron_expression: [
    { required: true, message: '请输入 Cron 表达式', trigger: 'blur' },
  ],
}

// Cron 表达式说明（仅高级模式展示）
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
    <!-- 定时任务配置 -->
    <el-card v-loading="scheduleLoading">
      <template #header>
        <div class="card-header">
          <span>定时任务配置</span>
        </div>
      </template>

      <el-form
        ref="scheduleFormRef"
        :model="scheduleConfig"
        :rules="scheduleRules"
        label-width="120px"
      >
        <el-form-item label="启用定时任务">
          <el-switch v-model="scheduleEnabled" />
        </el-form-item>

        <el-form-item label="执行频率">
          <el-select
            v-model="scheduleConfig.frequency"
            :disabled="!scheduleEnabled"
            style="width: 280px"
          >
            <el-option
              v-for="opt in frequencyOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
          <div class="tz-hint">
            所有执行时间均按<strong>北京时间（UTC+8）</strong>计算，与服务器所在时区无关。
          </div>
        </el-form-item>

        <!-- 每天定点 -->
        <el-form-item v-if="scheduleConfig.frequency === 'daily'" label="执行时间">
          <el-time-select
            v-model="scheduleConfig.hour"
            :disabled="!scheduleEnabled"
            start="00" step="01" end="23"
            placeholder="时" style="width: 110px"
          />
          <span style="margin: 0 6px">时</span>
          <el-time-select
            v-model="scheduleConfig.minute"
            :disabled="!scheduleEnabled"
            start="00" step="05" end="55"
            placeholder="分" style="width: 110px"
          />
          <span style="margin-left: 6px">分</span>
        </el-form-item>

        <!-- 每 N 小时 -->
        <el-form-item v-else-if="scheduleConfig.frequency === 'every_n_hours'" label="间隔小时">
          <el-input-number
            v-model="scheduleConfig.interval"
            :disabled="!scheduleEnabled"
            :min="1" :max="23" :step="1"
          />
          <span style="margin-left: 8px">小时执行一次</span>
        </el-form-item>

        <!-- 工作日定点 -->
        <el-form-item v-else-if="scheduleConfig.frequency === 'weekdays'" label="执行时间">
          <el-time-select
            v-model="scheduleConfig.hour"
            :disabled="!scheduleEnabled"
            start="00" step="01" end="23"
            placeholder="时" style="width: 110px"
          />
          <span style="margin: 0 6px">时</span>
          <el-time-select
            v-model="scheduleConfig.minute"
            :disabled="!scheduleEnabled"
            start="00" step="05" end="55"
            placeholder="分" style="width: 110px"
          />
          <span style="margin-left: 6px">分（周一至周五）</span>
        </el-form-item>

        <!-- 每周定点 -->
        <el-form-item v-else-if="scheduleConfig.frequency === 'weekly'" label="执行时间">
          <el-select
            v-model="scheduleConfig.weekday"
            :disabled="!scheduleEnabled"
            style="width: 110px"
          >
            <el-option
              v-for="opt in weekdayOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
          <el-time-select
            v-model="scheduleConfig.hour"
            :disabled="!scheduleEnabled"
            start="00" step="01" end="23"
            placeholder="时" style="width: 110px; margin-left: 8px"
          />
          <span style="margin: 0 6px">时</span>
          <el-time-select
            v-model="scheduleConfig.minute"
            :disabled="!scheduleEnabled"
            start="00" step="05" end="55"
            placeholder="分" style="width: 110px"
          />
          <span style="margin-left: 6px">分</span>
        </el-form-item>

        <!-- 每 N 分钟 -->
        <el-form-item v-else-if="scheduleConfig.frequency === 'every_n_minutes'" label="间隔分钟">
          <el-input-number
            v-model="scheduleConfig.interval"
            :disabled="!scheduleEnabled"
            :min="1" :max="59" :step="1"
          />
          <span style="margin-left: 8px">分钟执行一次</span>
        </el-form-item>

        <!-- 高级：自定义 Cron -->
        <el-form-item v-else-if="scheduleConfig.frequency === 'custom'" label="Cron 表达式" prop="cron_expression">
          <el-input
            v-model="scheduleConfig.cron_expression"
            placeholder="0 9 * * *"
            :disabled="!scheduleEnabled"
            style="width: 280px"
          />
          <div class="form-help">
            <pre>{{ cronHelp }}</pre>
          </div>
        </el-form-item>

        <!-- 实时预览：翻译后的 Cron + 下次执行时间 -->
        <el-form-item label="实际生效" v-if="scheduleEnabled">
          <el-descriptions :column="1" border size="small" style="width: 100%">
            <el-descriptions-item label="Cron 表达式">
              <code>{{ cronExpression }}</code>
            </el-descriptions-item>
            <el-descriptions-item label="中文说明">
              {{ humanDescription }}
            </el-descriptions-item>
            <el-descriptions-item label="下次执行">
              <div class="next-run-cell">
                <span>{{ nextRunText }}</span>
                <span v-if="!isBrowserCST" class="next-run-bj">
                  （北京时间 {{ nextRunBeijingText }}）
                </span>
              </div>
            </el-descriptions-item>
          </el-descriptions>
        </el-form-item>

        <el-form-item label="当前状态" v-else>
          <el-tag type="info">定时任务已关闭，点击上方开关可启用</el-tag>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            :icon="Check"
            @click="saveScheduleConfig"
          >
            保存配置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- API密钥配置（只读展示） -->
    <el-card>
      <template #header>
        <div class="card-header">
          <span>API密钥配置</span>
        </div>
      </template>

      <el-alert
        title="API密钥需要在后端环境变量中配置"
        type="info"
        :closable="false"
        show-icon
      >
        <template #default>
          <p>请在后端的 <code>.env</code> 文件中配置以下环境变量：</p>
          <ul>
            <li><code>ANTHROPIC_API_KEY</code> - Claude API密钥</li>
            <li><code>SERPAPI_KEY</code> - SerpAPI搜索密钥</li>
            <li><code>SMTP_*</code> - 邮件发送配置</li>
          </ul>
        </template>
      </el-alert>
    </el-card>

    <!-- 关于 -->
    <el-card>
      <template #header>
        <div class="card-header">
          <span>关于系统</span>
        </div>
      </template>

      <el-descriptions :column="1" border>
        <el-descriptions-item label="系统名称">
          JobSentinel
        </el-descriptions-item>
        <el-descriptions-item label="版本">
          1.0.0
        </el-descriptions-item>
        <el-descriptions-item label="技术栈">
          Vue 3 + Element Plus + FastAPI + OpenAI SDK
        </el-descriptions-item>
        <el-descriptions-item label="功能说明">
          JobSentinel - 基于AI的招聘信息自动搜索和分析系统，支持定时任务、邮件通知、数据导出等功能。
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<style scoped>
.settings {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.form-help {
  margin-top: 8px;
}

.form-help pre {
  margin: 0;
  font-size: 12px;
  color: #909399;
  line-height: 1.6;
  white-space: pre-wrap;
}

.tz-hint {
  margin-top: 6px;
  font-size: 12px;
  color: #909399;
  line-height: 1.6;
}

.next-run-cell {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: baseline;
}

.next-run-bj {
  font-size: 12px;
  color: #909399;
}

code {
  background-color: #f5f7fa;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
  color: #e6a23c;
}

ul {
  margin: 8px 0 0 0;
  padding-left: 20px;
}

li {
  margin-bottom: 4px;
}
</style>
