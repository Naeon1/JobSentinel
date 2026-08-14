# JobSentinel 系统处理流程（Pipeline）

> 5 分钟读懂：用户配置什么 → 大模型每一步做什么 → 结果如何入库。
>
> 配合 [README.md](../README.md) 食用，本文聚焦"系统内部是怎么跑的"。各模块技术细节请看 [FEATURES.md](FEATURES.md)，LLM 配置示例请看 [LLM_CONFIG.md](LLM_CONFIG.md)。

---

## 一图流

```
用户配置（公司 + 职位）
        │
        ▼
   ┌─────────────────────────────────────────┐
   │  阶段1 规划 ── LLM 设计搜索策略           │
   │  输入：公司+职位 JSON                     │
   │  输出：JSON 对象（queries + 平台 + 关键词） │
   │  约束：英文键名、≤8 条查询、强制 site:官网 │
   └─────────────────────────────────────────┘
        │
        ▼  queries
   ┌─────────────────────────────────────────┐
   │  阶段2 搜索 ── SerpAPI 真实查询（无 LLM） │
   │  输入：阶段1 的 queries                   │
   │  输出：汇总去重的搜索结果（title/link/..）│
   │  约束：按 link 去重，失败继续             │
   └─────────────────────────────────────────┘
        │
        ▼  raw results
   ┌─────────────────────────────────────────┐
   │  阶段3 梳理 ── LLM 提取岗位信息           │
   │  输入：搜索结果（按 8 条/批）             │
   │  输出：JSON 数组（岗位对象）              │
   │  约束：source_url 必填、只保留真实在招    │
   └─────────────────────────────────────────┘
        │
        ▼
   入库：按 (platform, source_url) 去重 → JobListing
```

整个流水线 LLM 出现两次（规划 + 梳理），搜索是确定性代码，最后写库。

---

## 三阶段速查

| 阶段 | LLM 做什么 | 输入 | 输出 | 关键约束 |
|------|-----------|------|------|---------|
| **规划** | 根据公司/职位特点，设计 3–8 条 Google 搜索词 | 公司+职位 JSON | `{"queries":[...], "target_platforms":[...], "include_keywords":[...], "exclude_keywords":[...], "rationale":"..."}` | 英文键名、≤8 条、若公司有官网则必须包含 `site:域名` 查询 |
| **搜索** | （不调 LLM）执行 SerpAPI 调用 | 阶段1 的 queries | 汇总去重的 `[{title, link, snippet}, ...]` | 按 link 去重；某条 query 失败不影响其他 |
| **梳理** | 从搜索结果中识别在招岗位，提取结构化字段 | 搜索结果（每批 8 条） | `[{job_title, is_open, source_url, location, salary, skills, ...}, ...]` | `source_url` 为空的一律不输出；只保留与目标公司职位相关的真实在招信息；不可臆造薪资/技能 |

---

## 用户的配置如何变成 LLM 输入

LLM 不直接读数据库，而是拿到 SearchService 整理好的两个 dict：

- **公司 dict**：`name / aliases / website / career_page / industry`
- **职位 dict**：`title / keywords / exclude_keywords / locations / experience_level`

特别之处：系统会从 `website` 自动抽主域名，强制让 LLM 至少输出一条 `site:域名` 查询，保证官方招聘页被覆盖。如果公司还填了 `career_page`，会进一步要求一条指向它的查询词。

---

## LLM 输出的统一护栏

三个阶段的 LLM 调用都走同一套底层方法：

1. **流式调用**（`stream=True`） — 规避第三方中转站 SSE 心跳污染响应体。
2. **指数退避重试** — 最多 4 次，2s 起每次 +2s。仅对真正的瞬时故障重试，鉴权/参数错误直接抛。
3. **截断检测** — `finish_reason == "length"` 即被 `max_tokens` 截断，结果可能不完整，会写入步骤日志。

兜底机制：

- 阶段1 LLM 完全没产出有效 queries → 退回基础模板（"公司 职位 招聘" 等），保证流水线不中断。
- 阶段3 某一批 LLM 失败 → 该批返回 `[]`，其他批继续。
- 阶段3 任一批输出超长被截断 → 控制台告警 + 可视化页面标记 `truncated: true`。

---

## 任务如何被触发与推进

不管手动（`/api/tasks/run`）还是定时（APScheduler），最终都走同一条路径：

1. **预创建任务** — `SearchService.prepare_batch_tasks` 一次性把本批次所有 `SearchTask` 写入数据库（`status=planning`），返回 `task_ids`，前端立即可以开始轮询。
2. **后台异步执行** — `run_existing_tasks(task_ids)` 在 FastAPI 线程池 / 调度器线程里逐条跑 `_execute_task`。
3. **分阶段写进度** — 每进入/离开一个阶段就更新 `current_step / progress`，并往 `steps_log` JSON 数组追加一条详细日志（包含该阶段的 prompt、LLM 原始输出、命中明细等），前端「执行过程」页能逐步展开复盘。

进度推进：`planning 0→20%` → `searching 25→55%` → `extracting 60→85%` → `done 100%`。

---

## 结果如何入库

`_save_jobs` 在阶段3 之后被调用：

- `source_url` 为空 → **直接丢弃**（阶段3 已过滤一轮，这里再兜底一次）。
- 按 `(source_platform, md5(source_url))` 去重：命中则更新旧记录，未命中则新建。
- `is_open` 归一化为 `true / false / unknown` 三态字符串。
- 最终回填 `task.jobs_found = saved_count`，任务标 `completed`。

返回统计 `{saved, duplicated, skipped_no_url, failed}` 写入最后一条步骤日志。

---

## 端到端时序

```
T+0s    用户点搜索 / 定时 cron 触发
T+0.1s  预创建 SearchTask，返回 task_ids
T+0.2s  前端开始轮询
T+1s    阶段1：LLM 规划，产出 6 条 queries      (progress 5→20)
T+10s   阶段2：SerpAPI 跑完，汇总去重 38 条       (progress 25→55)
T+15s   阶段3：LLM 分 5 批梳理，提取 7 条岗位     (progress 60→85)
T+15.5s 入库：去重后 6 条写入 JobListing         (progress →100)
T+16s   任务完成；自动调用 EmailService 发送搜索报告（落 EmailLog）
```

---

## 一句话总结

**用户配置公司+职位 → LLM 设计搜索词 → SerpAPI 执行搜索 → LLM 从结果中提取在招岗位 → 按 URL 去重入库 → 自动发送邮件报告。** LLM 在前/后端出现两次，中间夹一段确定性搜索；每一步的 prompt、原始输出、命中明细都记录到 `steps_log`，方便事后复盘。
