<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Delete } from '@element-plus/icons-vue'
import { taskApi } from '../api'

const route = useRoute()
const router = useRouter()

// 从 URL 拿待观察的 task_ids；没有则展示最近任务
const taskIds = ref<string[]>([])
const tasks = ref<any[]>([])
const loading = ref(false)
const pollTimer = ref<any>(null)

const ACTIVE = ['planning', 'searching', 'extracting', 'running']

// ---- 加载 ----
const fetchAll = async () => {
  loading.value = true
  try {
    if (taskIds.value.length) {
      const list = await Promise.all(
        taskIds.value.map(async (id) => {
          try { return await taskApi.get(id) as any }
          catch { return null }
        })
      )
      tasks.value = list.filter(Boolean)
    } else {
      const data = await taskApi.list({ limit: 10 }) as any
      tasks.value = data.items || []
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const allDone = computed(() =>
  tasks.value.length > 0 && tasks.value.every(t => !ACTIVE.includes(t.status))
)

const poll = () => {
  if (pollTimer.value) return
  pollTimer.value = setInterval(fetchAll, 3000)
}
const stopPoll = () => {
  if (pollTimer.value) { clearInterval(pollTimer.value); pollTimer.value = null }
}

onMounted(async () => {
  const raw = route.query.ids as string | undefined
  if (raw) taskIds.value = raw.split(',').filter(Boolean)
  await fetchAll()
  if (!allDone.value) poll()
})
onBeforeUnmount(stopPoll)

// ---- 进度条状态 ----
const statusType = (s: string) =>
  ({ planning:'warning', searching:'warning', extracting:'warning', running:'warning',
     completed:'success', failed:'danger', pending:'info' })[s] || 'info'
const statusText = (s: string) =>
  ({ planning:'规划中', searching:'搜索中', extracting:'梳理中', running:'执行中',
     completed:'已完成', failed:'失败', pending:'待执行' })[s] || s

// ---- phase 分组：把 steps_log 按 phase 归类 ----
interface PhaseBlock {
  key: string
  title: string
  icon: string
  entries: any[]
}
const PHASE_MAP: Record<string, {title:string; icon:string}> = {
  planning:  { title: '阶段1 · AI 规划搜索策略',  icon: '🧠' },
  searching: { title: '阶段2 · 搜索引擎查询',      icon: '🔍' },
  extracting:{ title: '阶段3 · AI 提取岗位信息',  icon: '📊' },
  done:      { title: '结果统计',                   icon: '✅' },
}

function groupPhases(task: any): PhaseBlock[] {
  const logs: any[] = task.steps_log || []
  const map: Record<string, any[]> = {}
  for (const l of logs) {
    const key = l.step
    if (key === 'done') { map['done'] = map['done'] || []; map['done'].push(l); continue }
    if (!PHASE_MAP[key]) continue
    map[key] = map[key] || []
    map[key].push(l)
  }
  const order = ['planning', 'searching', 'extracting', 'done']
  return order
    .filter(k => map[k]?.length)
    .map(k => ({
      key: k,
      title: PHASE_MAP[k].title,
      icon: PHASE_MAP[k].icon,
      entries: map[k],
    }))
}

function getDetail(block: PhaseBlock): any | null {
  for (const e of block.entries) {
    if (e.detail) return e.detail
  }
  return null
}

function d(block: PhaseBlock, field?: string): any {
  const det = getDetail(block)
  if (!det) return field ? undefined : null
  return field ? det[field] : det
}

// 任务头部摘要
function taskSummary(task: any): string {
  const company = task.company_name || task.company_id?.slice(0, 8) || '?'
  const pos = task.position_title || task.position_config_id?.slice(0, 8) || '?'
  return `${company} × ${pos}`
}

// 限制文本长度展示
function truncate(s: string | null | undefined, n = 800): string {
  if (!s) return ''
  return s.length > n ? s.slice(0, n) + ' …（已截断）' : s
}

// 打开原文
const openSource = (url: string) => { if (url) window.open(url, '_blank') }

// 删除任务
const deleteTask = async (task: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除该任务吗？`,
      '警告',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'error' }
    )
    await taskApi.delete(task.id)
    ElMessage.success('已删除')
    tasks.value = tasks.value.filter((t) => t.id !== task.id)
  } catch (error) {
    // 用户取消
  }
}

// 阶段图标颜色映射
const phaseColor = (key: string) => {
  const colors: Record<string, string> = {
    planning: '#6366f1',
    searching: '#3b82f6',
    extracting: '#10b981',
    done: '#f59e0b',
  }
  return colors[key] || '#64748b'
}
</script>

<template>
  <div class="executions" v-loading="loading">
    <!-- 顶部信息栏 -->
    <div class="top-bar">
      <div class="bar-info">
        <template v-if="tasks.length">
          <span class="bar-label">本批次</span>
          <span class="bar-count">{{ tasks.length }}</span>
          <span class="bar-sep">个任务，</span>
          <span class="bar-success">{{ tasks.filter(t => t.status === 'completed').length }}</span>
          <span class="bar-sep">已完成，</span>
          <span class="bar-fail">{{ tasks.filter(t => t.status === 'failed').length }}</span>
          <span class="bar-sep">失败</span>
          <span v-if="!allDone" class="polling-indicator">
            <span class="dot"></span>实时刷新中
          </span>
        </template>
        <template v-else>
          <span class="bar-empty">暂无任务</span>
        </template>
      </div>
      <button class="refresh-btn" @click="fetchAll">
        <el-icon :size="16"><Refresh /></el-icon>
      </button>
    </div>

    <!-- 每个任务一张卡片 -->
    <div
      v-for="task in tasks"
      :key="task.id"
      class="task-card"
    >
      <!-- 卡片头部 -->
      <div class="task-header">
        <div class="header-left">
          <el-tag :type="statusType(task.status) as any" size="small" round class="status-tag">
            {{ statusText(task.status) }}
          </el-tag>
          <span class="task-title">{{ taskSummary(task) }}</span>
        </div>
        <div class="header-right">
          <!-- 进行中进度 -->
          <div v-if="ACTIVE.includes(task.status)" class="progress-wrap">
            <el-progress
              :percentage="task.progress || 0"
              :stroke-width="6"
              :status="task.status === 'failed' ? 'exception' : undefined"
              style="width: 160px"
            />
          </div>
          <!-- 完成跳转 -->
          <div v-if="task.jobs_found && task.status === 'completed'" class="result-btn">
            <button class="view-results-btn" @click="router.push('/jobs')">
              {{ task.jobs_found }} 条结果
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M5 12h14M12 5l7 7-7 7"/>
              </svg>
            </button>
          </div>
          <button class="delete-btn" @click="deleteTask(task)">
            <el-icon :size="14"><Delete /></el-icon>
          </button>
        </div>
      </div>

      <!-- 错误信息 -->
      <div v-if="task.status === 'failed' && task.error_message" class="error-banner">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        {{ task.error_message }}
      </div>

      <!-- 各阶段可折叠面板 -->
      <div class="phases">
        <div
          v-for="block in groupPhases(task)"
          :key="block.key"
          class="phase-item"
        >
          <div class="phase-header">
            <div class="phase-title-wrap">
              <span class="phase-icon">{{ block.icon }}</span>
              <span class="phase-title" :style="{ color: phaseColor(block.key) }">{{ block.title }}</span>
            </div>
            <div class="phase-tags">
              <span
                v-if="block.entries.some(e => e.status === 'error')"
                class="phase-tag error"
              >失败</span>
              <span
                v-else-if="block.entries.some(e => e.status === 'done')"
                class="phase-tag success"
              >完成</span>
              <span
                v-else-if="block.entries.some(e => e.status === 'start')"
                class="phase-tag processing"
              >执行中</span>
            </div>
          </div>

          <div class="phase-content">
            <!-- 通用 message -->
            <div v-for="(entry, ei) in block.entries" :key="ei" class="log-entry">
              <p class="log-msg">{{ entry.message }}</p>
            </div>

            <!-- 阶段1 Planning 细节 -->
            <template v-if="block.key === 'planning' && d(block)">
              <div class="detail-section">
                <div class="section-label">喂给 LLM 的 Prompt</div>
                <details class="code-block">
                  <summary>系统提示词</summary>
                  <pre class="pre-content">{{ truncate(d(block, 'system_prompt'), 3000) }}</pre>
                </details>
                <details class="code-block">
                  <summary>用户消息（公司 + 职位信息）</summary>
                  <pre class="pre-content">{{ truncate(d(block, 'user_message'), 3000) }}</pre>
                </details>
              </div>

              <div class="detail-section">
                <div class="section-label">LLM 原始输出</div>
                <pre class="pre-content output">{{ truncate(d(block, 'llm_raw_output'), 2000) }}</pre>
              </div>

              <div class="detail-section">
                <div class="section-label">生成的搜索策略</div>
                <div class="strategy-block">
                  <div class="strategy-row">
                    <span class="strategy-key">查询词</span>
                    <div class="strategy-tags">
                      <span v-for="q in (d(block, 'plan_queries') || [])" :key="q" class="query-tag">{{ q }}</span>
                    </div>
                  </div>
                  <div class="strategy-row">
                    <span class="strategy-key">目标平台</span>
                    <span class="strategy-val">{{ (d(block, 'target_platforms') || []).join('、') || '-' }}</span>
                  </div>
                  <div class="strategy-row">
                    <span class="strategy-key">关注关键词</span>
                    <span class="strategy-val">{{ (d(block, 'include_keywords') || []).join('、') || '-' }}</span>
                  </div>
                  <div class="strategy-row">
                    <span class="strategy-key">排除关键词</span>
                    <span class="strategy-val">{{ (d(block, 'exclude_keywords') || []).join('、') || '-' }}</span>
                  </div>
                  <div class="strategy-row" v-if="d(block, 'rationale')">
                    <span class="strategy-key">策略说明</span>
                    <span class="strategy-val">{{ d(block, 'rationale') }}</span>
                  </div>
                </div>
              </div>
            </template>

            <!-- 阶段2 Searching 细节 -->
            <template v-if="block.key === 'searching' && d(block)">
              <div class="detail-section">
                <div class="section-label">搜索统计</div>
                <div class="search-stats">
                  <span class="stat-chip">{{ d(block, 'queries_count') }} 条查询词</span>
                  <span class="stat-chip primary">汇总 {{ d(block, 'total_results') }} 条结果</span>
                </div>

                <details
                  v-for="(qd, qi) in (d(block, 'queries_detail') || [])"
                  :key="qi"
                  class="query-block"
                >
                  <summary>
                    <span class="query-text">{{ qd.query }}</span>
                    <span class="query-stats">
                      {{ qd.new_count }} 新 / {{ qd.raw_count }} 原始
                      <span v-if="qd.error" class="query-error-badge">失败</span>
                    </span>
                  </summary>

                  <div v-if="qd.error" class="query-error">
                    错误：{{ qd.error }}
                  </div>

                  <table v-if="qd.samples?.length" class="samples-table">
                    <thead>
                      <tr><th>标题</th><th>链接</th><th>摘要</th></tr>
                    </thead>
                    <tbody>
                      <tr v-for="(s, si) in qd.samples" :key="si">
                        <td>{{ s.title }}</td>
                        <td><a :href="s.link" target="_blank" class="link">{{ s.link }}</a></td>
                        <td class="snippet">{{ s.snippet }}</td>
                      </tr>
                    </tbody>
                  </table>
                </details>
              </div>
            </template>

            <!-- 阶段3 Extracting 细节 -->
            <template v-if="block.key === 'extracting' && d(block)">
              <div class="detail-section">
                <div class="section-label">系统提示词（岗位提取规则）</div>
                <details class="code-block">
                  <pre class="pre-content">{{ truncate(d(block, 'system_prompt'), 3000) }}</pre>
                </details>
              </div>

              <div class="detail-section">
                <div class="section-label">分批执行详情（ {{ d(block, 'batch_count') }} 批）</div>
                <details
                  v-for="(b, bi) in (d(block, 'batches') || [])"
                  :key="bi"
                  class="batch-block"
                >
                  <summary>
                    第 {{ b.index }} 批：
                    输入 {{ b.input_count }} 条 → 提取 {{ b.output_count }} 条
                    <span v-if="b.truncated" class="batch-warn">输出截断 ({{ b.finish_reason }})</span>
                    <span v-else class="batch-ok">{{ b.finish_reason }}</span>
                  </summary>
                  <details class="code-block">
                    <summary>本批输入（用户消息）</summary>
                    <pre class="pre-content">{{ truncate(b.user_message, 3000) }}</pre>
                  </details>
                  <details class="code-block">
                    <summary>LLM 输出</summary>
                    <pre class="pre-content output">{{ truncate(b.raw_output, 3000) }}</pre>
                  </details>
                </details>

                <div class="extract-summary" v-if="(d(block, 'batches') || []).length">
                  共提取 <strong>{{ d(block, 'extracted_count') }}</strong> 条岗位（含多批去重前）
                </div>
              </div>
            </template>

            <!-- done 细节 -->
            <template v-if="block.key === 'done' && d(block)">
              <div class="detail-section">
                <div class="result-stats">
                  <div class="stat-item">
                    <span class="stat-label">AI 提取数</span>
                    <span class="stat-value">{{ d(block, 'input_count') }}</span>
                  </div>
                  <div class="stat-item highlight">
                    <span class="stat-label">入库数</span>
                    <span class="stat-value">{{ d(block, 'saved_count') }}</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-label">更新旧记录</span>
                    <span class="stat-value">{{ d(block, 'duplicated_count') }}</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-label">无链接丢弃</span>
                    <span class="stat-value">{{ d(block, 'skipped_no_url_count') }}</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-label">入库失败</span>
                    <span class="stat-value danger">{{ d(block, 'failed_count') }}</span>
                  </div>
                </div>
              </div>
            </template>
          </div>
        </div>

        <!-- 无 steps_log 时 -->
        <div v-if="!task.steps_log || task.steps_log === '[]'" class="empty-logs">
          暂无执行日志（任务尚未开始或已清理）
        </div>
      </div>
    </div>

    <!-- 无任务时 -->
    <div v-if="!loading && !tasks.length" class="empty-state">
      <div class="empty-icon">📭</div>
      <p>暂无执行中的任务</p>
      <button class="go-dashboard-btn" @click="router.push('/dashboard')">
        返回仪表盘
      </button>
    </div>
  </div>
</template>

<style scoped>
.executions {
  max-width: 1000px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* ── 顶部信息栏 ── */
.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  background: var(--js-card-bg);
  border: 1px solid var(--js-card-border);
  border-radius: var(--js-radius-lg);
  box-shadow: var(--js-card-shadow);
}

.bar-info {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: var(--js-text-secondary);
}

.bar-label { font-weight: 600; color: var(--js-text-primary); }
.bar-count { font-weight: 700; color: var(--js-primary); }
.bar-success { font-weight: 700; color: var(--js-success); }
.bar-fail { font-weight: 700; color: var(--js-danger); }
.bar-sep { color: var(--js-text-tertiary); }
.bar-empty { color: var(--js-text-tertiary); }

.polling-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--js-primary);
  font-weight: 500;
  margin-left: 8px;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--js-primary);
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(0.8); }
}

.refresh-btn {
  width: 32px;
  height: 32px;
  border-radius: var(--js-radius-sm);
  border: 1px solid var(--js-card-border);
  background: transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--js-text-secondary);
  transition: all var(--js-transition);
}

.refresh-btn:hover {
  background: var(--js-page-bg);
  color: var(--js-text-primary);
}

/* ── 任务卡片 ── */
.task-card {
  background: var(--js-card-bg);
  border: 1px solid var(--js-card-border);
  border-radius: var(--js-radius-lg);
  overflow: hidden;
  box-shadow: var(--js-card-shadow);
}

.task-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--js-card-border);
  gap: 16px;
  flex-wrap: wrap;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-tag {
  font-weight: 600;
}

.task-title {
  font-weight: 700;
  color: var(--js-text-primary);
  font-size: 15px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-wrap {
  display: flex;
  align-items: center;
}

.result-btn .view-results-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: var(--js-primary);
  color: #fff;
  border: none;
  border-radius: var(--js-radius-sm);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--js-transition);
}

.view-results-btn:hover {
  background: var(--js-primary-light);
}

.delete-btn {
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--js-text-tertiary);
  transition: all var(--js-transition);
}

.delete-btn:hover {
  background: rgba(239, 68, 68, 0.1);
  color: var(--js-danger);
}

/* ── 错误横幅 ── */
.error-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: rgba(239, 68, 68, 0.08);
  color: var(--js-danger);
  font-size: 13px;
}

/* ── 阶段折叠 ── */
.phases {
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.phase-item {
  border: 1px solid var(--js-card-border);
  border-radius: var(--js-radius-md);
  overflow: hidden;
}

.phase-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--js-page-bg);
  cursor: pointer;
}

details {
  cursor: pointer;
}

details > summary {
  list-style: none;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: #f8fafc;
  border-bottom: 1px solid var(--js-card-border);
}

details > summary::-webkit-details-marker { display: none; }

details[open] > summary {
  border-bottom-color: var(--js-primary-alpha);
}

.phase-title-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.phase-icon { font-size: 16px; }

.phase-title {
  font-weight: 700;
  font-size: 14px;
}

.phase-tags {
  display: flex;
  gap: 6px;
}

.phase-tag {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}

.phase-tag.success {
  background: rgba(16, 185, 129, 0.1);
  color: var(--js-success);
}

.phase-tag.error {
  background: rgba(239, 68, 68, 0.1);
  color: var(--js-danger);
}

.phase-tag.processing {
  background: rgba(245, 158, 11, 0.1);
  color: var(--js-warning);
}

.phase-content {
  padding: 0;
}

.log-entry {
  padding: 10px 16px;
  border-bottom: 1px solid var(--js-card-border);
}

.log-msg {
  margin: 0;
  font-size: 13px;
  color: var(--js-text-secondary);
}

/* ── 详情区块 ── */
.detail-section {
  padding: 12px 16px;
  border-bottom: 1px solid var(--js-card-border);
}

.section-label {
  font-size: 12px;
  font-weight: 700;
  color: var(--js-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: 8px;
}

.pre-content {
  white-space: pre-wrap;
  word-break: break-all;
  font-size: 12px;
  line-height: 1.7;
  color: var(--js-text-secondary);
  background: #f8fafc;
  padding: 12px 14px;
  border-radius: var(--js-radius-sm);
  margin: 8px 0 0 0;
  font-family: 'Cascadia Code', 'Fira Code', Consolas, monospace;
  max-height: 400px;
  overflow-y: auto;
}

.pre-content.output {
  background: #1e1e2e;
  color: #cdd6f4;
}

/* ── 策略块 ── */
.strategy-block {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.strategy-row {
  display: flex;
  gap: 12px;
  font-size: 13px;
}

.strategy-key {
  min-width: 80px;
  font-weight: 700;
  color: var(--js-text-primary);
  flex-shrink: 0;
}

.strategy-val {
  color: var(--js-text-secondary);
}

.strategy-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.query-tag {
  display: inline-flex;
  padding: 2px 8px;
  background: var(--js-primary-alpha);
  color: var(--js-primary);
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

/* ── 搜索统计 ── */
.search-stats {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.stat-chip {
  display: inline-flex;
  padding: 4px 10px;
  background: #f1f5f9;
  color: var(--js-text-secondary);
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.stat-chip.primary {
  background: var(--js-primary-alpha);
  color: var(--js-primary);
}

.query-block {
  border: 1px solid var(--js-card-border);
  border-radius: var(--js-radius-sm);
  margin-bottom: 8px;
  overflow: hidden;
}

.query-block > summary {
  font-size: 13px;
}

.query-text {
  font-family: monospace;
  color: var(--js-primary);
  font-weight: 600;
}

.query-stats {
  margin-left: auto;
  font-size: 12px;
  color: var(--js-text-tertiary);
}

.query-error-badge {
  color: var(--js-danger);
  font-weight: 600;
}

.query-error {
  padding: 8px 16px;
  font-size: 12px;
  color: var(--js-danger);
  background: rgba(239, 68, 68, 0.05);
}

.samples-table {
  width: 100%;
  font-size: 12px;
  border-collapse: collapse;
}

.samples-table th,
.samples-table td {
  border: 1px solid var(--js-card-border);
  padding: 8px 10px;
  vertical-align: top;
  text-align: left;
}

.samples-table th {
  background: #f8fafc;
  font-weight: 700;
  color: var(--js-text-secondary);
}

.snippet {
  color: var(--js-text-tertiary);
  max-width: 300px;
}

.link {
  color: var(--js-primary);
  word-break: break-all;
}

/* ── 分批块 ── */
.batch-block {
  border: 1px solid var(--js-card-border);
  border-radius: var(--js-radius-sm);
  margin-bottom: 8px;
  overflow: hidden;
}

.batch-warn {
  color: var(--js-warning);
  font-weight: 600;
  font-size: 12px;
}

.batch-ok {
  color: var(--js-success);
  font-size: 12px;
}

.extract-summary {
  margin-top: 10px;
  font-size: 13px;
  color: var(--js-text-secondary);
}

.extract-summary strong {
  color: var(--js-primary);
}

/* ── 入库统计 ── */
.result-stats {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
}

@media (max-width: 768px) {
  .result-stats { grid-template-columns: repeat(3, 1fr); }
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px;
  background: var(--js-page-bg);
  border-radius: var(--js-radius-md);
  text-align: center;
}

.stat-item.highlight {
  background: var(--js-primary-alpha);
}

.stat-item .stat-label {
  font-size: 11px;
  color: var(--js-text-tertiary);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.stat-item .stat-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--js-text-primary);
}

.stat-item.highlight .stat-value {
  color: var(--js-primary);
}

.stat-item .stat-value.danger {
  color: var(--js-danger);
}

/* ── 空状态 ── */
.empty-logs {
  padding: 40px;
  text-align: center;
  color: var(--js-text-tertiary);
  font-size: 14px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  background: var(--js-card-bg);
  border: 1px solid var(--js-card-border);
  border-radius: var(--js-radius-lg);
  box-shadow: var(--js-card-shadow);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-state p {
  margin: 0 0 20px 0;
  font-size: 16px;
  color: var(--js-text-secondary);
}

.go-dashboard-btn {
  padding: 10px 20px;
  background: var(--js-primary);
  color: #fff;
  border: none;
  border-radius: var(--js-radius-sm);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--js-transition);
}

.go-dashboard-btn:hover {
  background: var(--js-primary-light);
}
</style>
