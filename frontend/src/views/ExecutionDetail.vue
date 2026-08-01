<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { View, Refresh, Link, Delete } from '@element-plus/icons-vue'
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
      // 无 ids 参数：拉最近 10 条
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
  extracting:{ title: '阶段3 · AI 提取岗位信息',    icon: '📊' },
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

// 找 phase 块里带 detail 的条目
function getDetail(block: PhaseBlock): any | null {
  for (const e of block.entries) {
    if (e.detail) return e.detail
  }
  return null
}

// 模板里访问 detail 属性的安全方式（避免 ?. 在 Vue 模板 TS 编译器里不稳定）
// 用法：{{ d(block, 'system_prompt') }} 或 v-if="d(block)"
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
    // 从列表中移除
    tasks.value = tasks.value.filter((t) => t.id !== task.id)
  } catch (error) {
    // 用户取消
  }
}
</script>

<template>
  <div class="executions" v-loading="loading">
    <!-- 顶部信息栏 -->
    <div class="top-bar">
      <div class="info">
        <span v-if="tasks.length">
          本批次共 <b>{{ tasks.length }}</b> 个任务，
          已完成 <b>{{ tasks.filter(t => t.status === 'completed').length }}</b>，
          失败 <b>{{ tasks.filter(t => t.status === 'failed').length }}</b>
          <span v-if="!allDone">（实时刷新中…）</span>
        </span>
        <span v-else>暂无任务</span>
      </div>
      <el-button text @click="fetchAll"><el-icon><Refresh /></el-icon></el-button>
    </div>

    <!-- 每个任务一张卡片 -->
    <el-card v-for="task in tasks" :key="task.id" class="task-card" shadow="hover">
      <template #header>
        <div class="task-header">
          <div class="task-meta">
            <el-tag :type="statusType(task.status) as any" size="small" class="status-tag">
              {{ statusText(task.status) }}
            </el-tag>
            <span class="task-title">{{ taskSummary(task) }}</span>
            <span class="task-id">{{ task.id }}</span>
          </div>
          <div class="task-progress" v-if="ACTIVE.includes(task.status)">
            <el-progress
              :percentage="task.progress || 0"
              :stroke-width="8"
              :status="task.status === 'failed' ? 'exception' : undefined"
              style="width: 200px"
            />
          </div>
          <div class="task-result" v-if="task.jobs_found && task.status === 'completed'">
            <el-button type="primary" link @click="router.push('/jobs')">
              {{ task.jobs_found }} 条结果 →
            </el-button>
          </div>
          <el-button
            type="danger"
            link
            :icon="Delete"
            @click="deleteTask(task)"
            class="task-delete-btn"
          />
        </div>
      </template>

      <!-- 错误信息 -->
      <el-alert
        v-if="task.status === 'failed' && task.error_message"
        :title="'任务失败：' + task.error_message"
        type="error"
        :closable="false"
        show-icon
        style="margin-bottom: 16px"
      />

      <!-- 各阶段可折叠面板 -->
      <el-collapse class="phase-collapse">
        <el-collapse-item
          v-for="block in groupPhases(task)"
          :key="block.key"
          :name="block.key"
        >
          <template #title>
            <span class="phase-title">{{ block.icon }} {{ block.title }}</span>
            <el-tag
              v-if="block.entries.some(e => e.status === 'error')"
              type="danger" size="small" style="margin-left: 8px"
            >失败</el-tag>
            <el-tag
              v-else-if="block.entries.some(e => e.status === 'done')"
              type="success" size="small" style="margin-left: 8px"
            >完成</el-tag>
            <el-tag
              v-else-if="block.entries.some(e => e.status === 'start')"
              type="warning" size="small" style="margin-left: 8px"
            >执行中</el-tag>
          </template>

          <div class="phase-content">
            <!-- 通用：每条 log 的 message -->
            <div v-for="(entry, ei) in block.entries" :key="ei" class="log-entry">
              <div class="log-msg">{{ entry.message }}</div>
            </div>

            <!-- ====== 阶段1 Planning 细节 ====== -->
            <template v-if="block.key === 'planning' && d(block)">
              <el-divider content-position="left">喂给 LLM 的 Prompt</el-divider>
              <el-collapse class="sub-collapse">
                <el-collapse-item title="系统提示词">
                  <pre class="pre-block">{{ truncate(d(block, 'system_prompt'), 3000) }}</pre>
                </el-collapse-item>
                <el-collapse-item title="用户消息（公司 + 职位信息）">
                  <pre class="pre-block">{{ truncate(d(block, 'user_message'), 3000) }}</pre>
                </el-collapse-item>
              </el-collapse>

              <el-divider content-position="left">LLM 原始输出</el-divider>
              <pre class="pre-block output-block">{{ truncate(d(block, 'llm_raw_output'), 2000) }}</pre>

              <el-divider content-position="left">生成的搜索策略</el-divider>
              <div class="strategy-block">
                <div class="strategy-item"><b>查询词：</b>
                  <el-tag v-for="q in (d(block, 'plan_queries') || [])" :key="q" size="small" style="margin: 2px">{{ q }}</el-tag>
                </div>
                <div class="strategy-item"><b>目标平台：</b>{{ (d(block, 'target_platforms') || []).join('、') || '-' }}</div>
                <div class="strategy-item"><b>关注关键词：</b>{{ (d(block, 'include_keywords') || []).join('、') || '-' }}</div>
                <div class="strategy-item"><b>排除关键词：</b>{{ (d(block, 'exclude_keywords') || []).join('、') || '-' }}</div>
                <div class="strategy-item" v-if="d(block, 'rationale')"><b>策略说明：</b>{{ d(block, 'rationale') }}</div>
              </div>
            </template>

            <!-- ====== 阶段2 Searching 细节 ====== -->
            <template v-if="block.key === 'searching' && d(block)">
              <el-divider content-position="left">搜索明细</el-divider>
              <div class="search-stats">
                <el-tag type="info" size="small">共 {{ d(block, 'queries_count') }} 条查询词</el-tag>
                <el-tag type="success" size="small" style="margin-left: 8px">汇总 {{ d(block, 'total_results') }} 条网页结果</el-tag>
              </div>

              <el-collapse class="sub-collapse">
                <el-collapse-item
                  v-for="(qd, qi) in (d(block, 'queries_detail') || [])"
                  :key="qi"
                  :name="qi"
                >
                  <template #title>
                    <span class="query-title">{{ qd.query }}</span>
                    <el-tag size="small" style="margin-left: 8px">
                      {{ qd.new_count }} 新 / {{ qd.raw_count }} 原始
                    </el-tag>
                    <el-tag v-if="qd.error" type="danger" size="small" style="margin-left: 4px">失败</el-tag>
                  </template>

                  <div v-if="qd.error" class="query-error">错误：{{ qd.error }}</div>

                  <table v-if="qd.samples?.length" class="samples-table">
                    <thead><tr><th>标题</th><th>链接</th><th>摘要</th></tr></thead>
                    <tbody>
                      <tr v-for="(s, si) in qd.samples" :key="si">
                        <td>{{ s.title }}</td>
                        <td><a :href="s.link" target="_blank" class="link">{{ s.link }}</a></td>
                        <td class="snippet">{{ s.snippet }}</td>
                      </tr>
                    </tbody>
                  </table>
                </el-collapse-item>
              </el-collapse>
            </template>

            <!-- ====== 阶段3 Extracting 细节 ====== -->
            <template v-if="block.key === 'extracting' && d(block)">
              <el-divider content-position="left">喂给 LLM 的 Prompt</el-divider>
              <el-collapse class="sub-collapse">
                <el-collapse-item title="系统提示词（岗位提取规则）">
                  <pre class="pre-block">{{ truncate(d(block, 'system_prompt'), 3000) }}</pre>
                </el-collapse-item>
              </el-collapse>

              <el-divider content-position="left">分批执行详情（{{ d(block, 'batch_count') }} 批）</el-divider>
              <el-collapse class="sub-collapse">
                <el-collapse-item
                  v-for="(b, bi) in (d(block, 'batches') || [])"
                  :key="bi"
                  :name="bi"
                >
                  <template #title>
                    第 {{ b.index }} 批：
                    输入 {{ b.input_count }} 条 → 提取 {{ b.output_count }} 条
                    <el-tag v-if="b.truncated" type="warning" size="small" style="margin-left: 8px">
                      输出被截断 ({{ b.finish_reason }})
                    </el-tag>
                    <el-tag v-else type="success" size="small" style="margin-left: 8px">
                      {{ b.finish_reason }}
                    </el-tag>
                  </template>

                  <el-collapse class="sub-collapse">
                    <el-collapse-item title="本批输入（用户消息）">
                      <pre class="pre-block">{{ truncate(b.user_message, 3000) }}</pre>
                    </el-collapse-item>
                    <el-collapse-item title="LLM 输出">
                      <pre class="pre-block output-block">{{ truncate(b.raw_output, 3000) }}</pre>
                    </el-collapse-item>
                  </el-collapse>
                </el-collapse-item>
              </el-collapse>

              <div class="extract-summary" v-if="(d(block, 'batches') || []).length">
                共 <b>{{ d(block, 'extracted_count') }}</b> 条岗位（含多批去重前结果）
              </div>
            </template>

            <!-- ====== done 细节 ====== -->
            <template v-if="block.key === 'done' && d(block)">
              <div class="done-stats">
                <el-descriptions :column="2" border size="small">
                  <el-descriptions-item label="AI 提取数">{{ d(block, 'input_count') }}</el-descriptions-item>
                  <el-descriptions-item label="入库数">
                    <span class="stat-highlight">{{ d(block, 'saved_count') }}</span>
                  </el-descriptions-item>
                  <el-descriptions-item label="更新旧记录">{{ d(block, 'duplicated_count') }}</el-descriptions-item>
                  <el-descriptions-item label="无链接丢弃">{{ d(block, 'skipped_no_url_count') }}</el-descriptions-item>
                  <el-descriptions-item label="入库失败">{{ d(block, 'failed_count') }}</el-descriptions-item>
                </el-descriptions>
              </div>
            </template>
          </div>
        </el-collapse-item>
      </el-collapse>

      <!-- 无 steps_log 时的兜底 -->
      <el-empty
        v-if="!task.steps_log || task.steps_log === '[]'"
        description="暂无执行日志（任务尚未开始或已清理）"
        :image-size="60"
      />
    </el-card>
  </div>
</template>

<style scoped>
.executions {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fff;
  padding: 12px 20px;
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0,0,0,.06);
}
.top-bar .info { font-size: 14px; color: #606266; }
.top-bar .info b { color: #303133; }

.task-card { margin-bottom: 0; }

.task-header {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}
.task-meta { display: flex; align-items: center; gap: 10px; flex: 1; }
.task-title { font-weight: 600; color: #303133; font-size: 15px; }
.task-id   { font-size: 12px; color: #c0c4cc; }
.task-result { margin-left: auto; }
.task-delete-btn { margin-left: 8px; }

.phase-collapse { border: none; }
.phase-title { font-size: 14px; font-weight: 600; color: #303133; }

.phase-content { display: flex; flex-direction: column; gap: 8px; }
.log-msg { font-size: 13px; color: #606266; }

/* 子折叠面板 */
.sub-collapse { margin: 8px 0; border: 1px solid #ebeef5; border-radius: 4px; }
.sub-collapse :deep(.el-collapse-item__header) {
  background: #f9fafc; padding: 0 12px; font-size: 13px;
}
.sub-collapse :deep(.el-collapse-item__wrap) { padding: 0; }

/* pre 格式块 */
.pre-block {
  white-space: pre-wrap;
  word-break: break-all;
  font-size: 12px;
  line-height: 1.7;
  color: #4e5969;
  background: #f5f7fa;
  padding: 12px 14px;
  border-radius: 4px;
  max-height: 500px;
  overflow-y: auto;
  margin: 0;
  font-family: 'Cascadia Code', 'Fira Code', Consolas, monospace;
}
.output-block { background: #1e1e2e; color: #cdd6f4; }

/* 策略 */
.strategy-block { display: flex; flex-direction: column; gap: 6px; }
.strategy-item { font-size: 13px; color: #606266; }

/* 搜索统计 */
.search-stats { margin-bottom: 8px; }

/* 搜索样例表 */
.samples-table {
  width: 100%; font-size: 12px; border-collapse: collapse; margin-top: 8px;
}
.samples-table th, .samples-table td {
  border: 1px solid #ebeef5; padding: 6px 8px; vertical-align: top;
}
.samples-table th { background: #f9fafc; font-weight: 600; text-align: left; }
.snippet { color: #909399; max-width: 400px; }
.link { color: #409eff; word-break: break-all; }
.query-title { font-family: monospace; color: #409eff; }
.query-error { color: #f56c6c; font-size: 13px; }

/* 提取汇总 */
.extract-summary { font-size: 13px; color: #606266; margin-top: 8px; }

/* 入库统计 */
.done-stats { max-width: 480px; }
.stat-highlight { color: #67c23a; font-weight: 700; font-size: 16px; }
</style>
