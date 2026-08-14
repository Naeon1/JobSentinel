# JobSentinel 功能与技术实现文档

> 本文档系统介绍 JobSentinel 各功能模块,并说明每个模块采用的实现技术、核心代码位置与设计要点。
> 配合 [README.md](../README.md) 食用,README 偏概览与上手,本文档偏"功能拆解 + 技术细节"。
> 想快速了解系统处理流程请阅读 [PIPELINE.md](PIPELINE.md)。

---

## 目录

- [一、整体架构与功能全景](#一整体架构与功能全景)
- [二、核心功能一:LLM 主导的三阶段搜索流水线](#二核心功能一llm-主导的三阶段搜索流水线)
- [三、核心功能二:任务执行可视化(steps_log 全链路追踪)](#三核心功能二任务执行可视化steps_log-全链路追踪)
- [四、核心功能三:公司 × 职位监测清单管理](#四核心功能三公司--职位监测清单管理)
- [五、核心功能四:招聘信息检索与去重入库](#五核心功能四招聘信息检索与去重入库)
- [六、核心功能五:基于 APScheduler 的定时任务调度](#六核心功能五基于-apscheduler-的定时任务调度)
- [七、核心功能六:多 LLM 服务兼容(OpenAI 兼容接口)](#七核心功能六多-llm-服务兼容openai-兼容接口)
- [八、核心功能七:搜索完成邮件通知](#八核心功能七搜索完成邮件通知)
- [九、核心功能八:仪表盘统计](#九核心功能八仪表盘统计)
- [十、前端九大页面功能详解](#十前端九大页面功能详解)
- [十一、部署与工程化](#十一部署与工程化)
- [附录:技术栈速查表](#附录技术栈速查表)

---

## 一、整体架构与功能全景

JobSentinel 是"基于 AI 的招聘信息自动搜索与监测系统"。它维护一份「公司 × 职位」监测清单,按需手动触发或 cron 定时触发,由 LLM 自动规划搜索查询、调用 SerpAPI 搜索、再由 LLM 提取结构化在招岗位信息,统一入库供筛选查看。

```
┌───────────────────────────────────────────────────────────────┐
│  前端 (Vue 3 + Element Plus, 端口 5173)                          │
│  仪表盘/公司/职位/招聘/任务历史/执行过程/邮件通知/设置/配置测试 │
└───────────────┬───────────────────────────────────────────────┘
                │ axios → /api 代理 (Vite)
┌───────────────▼───────────────────────────────────────────────┐
│  后端 (FastAPI + Uvicorn, 端口 8000)                            │
│  ┌────────────┐  ┌───────────────┐  ┌──────────────────────┐   │
│  │ api 路由层  │→ │ services 编排 │→ │ agents 三阶段 Agent  │   │
│  │companies   │  │ search_service│  │  plan→search→extract │   │
│  │positions   │  │ email_service │  └──────────┬───────────┘   │
│  │jobs/tasks  │  └──────┬────────┘             │               │
│  │schedules   │         │                      ▼               │
│  │email/l_logs│         │              ┌──────────────┐        │
│  └────────────┘         ▼              │ tools        │        │
│  ┌────────────┐  ┌────────────┐        │ serpapi_search│       │
│  │scheduler   │  │ models     │        └──────┬───────┘        │
│  │ APScheduler│  │ SQLAlchemy │               │                │
│  └────────────┘  └─────┬──────┘               │                │
└────────────────────────┼──────────────────────┼────────────────┘
                         ▼                      ▼
                   SQLite/PostgreSQL      SerpAPI(Google) + LLM API
                                                +
                                          SMTP 邮件服务
```

**八大核心功能**:
1. LLM 三阶段搜索流水线(规划→搜索→梳理)
2. 任务执行可视化(全链路 steps_log 追踪)
3. 公司 × 职位监测清单管理(CRUD + 软删除/启用)
4. 招聘信息检索与去重入库
5. APScheduler 定时任务调度(含热更新)
6. 多 LLM 兼容(OpenAI 兼容接口 + 流式调用)
7. 搜索完成邮件通知(SMTP + HTML 模板 + EmailLog 历史记录)
8. 仪表盘统计

后端代码组织([backend/app/](../backend/app/))严格分层:`api`(路由) → `services`(编排) → `agents`(AI 流水线) → `tools`(外部工具) → `models`(ORM) → `schemas`(Pydantic) → `scheduler`(定时) → `core`(配置)。

---

## 二、核心功能一:LLM 主导的三阶段搜索流水线

> 这是整个系统的"心脏"。相比早期硬编码查询词模板,本方案让 LLM 真正主导搜索策略,更贴合"监测岗位开放情况"的目标。
> 实现文件:[backend/app/agents/search_agent.py](../backend/app/agents/search_agent.py)

### 阶段 1:规划(plan_search)— LLM 输出结构化搜索策略

**做什么**:把公司(名称/别名/官网/招聘页/行业)+ 职位(职位名/关键词/排除词/目标城市/经验级别)信息交给 LLM,输出一份结构化搜索策略 JSON,包含 `queries`(查询词)、`target_platforms`(预期命中平台)、`include_keywords`、`exclude_keywords`、`rationale`(思路)。

**实现技术**:
- **OpenAI SDK 同步 client**(`openai.OpenAI`),见 [search_agent.py:97-105](../backend/app/agents/search_agent.py#L97-L105)。`temperature=0` 保证策略稳定可复现。
- **强约束系统提示词** `PLAN_SYSTEM_PROMPT`([search_agent.py:24-50](../backend/app/agents/search_agent.py#L24-L50)):明确要求"键名必须用英文、严格 JSON、直接以 `{` 开头",并给出示例。
- **`site:` 限定查询生成**:`_build_plan_user_message`([search_agent.py:325-377](../backend/app/agents/search_agent.py#L325-L377))从官网 URL 正则提取主域名,在用户消息里硬性要求 LLM **必须**包含至少一条 `site:<域名>` 查询以覆盖公司自有招聘页,确保官方岗位不被漏掉。
- **JSON 解析兜底** `_parse_plan_output`([search_agent.py:396-441](../backend/app/agents/search_agent.py#L396-L441)):去除 markdown 代码块标记 → 正则提取 `{...}` → `json.loads`;并通过 `key_aliases` 映射兼容 LLM 偶发回中文键名("查询"/"理由"等)。
- **三重兜底**:LLM 没给 `queries` → 走 `_fallback_queries` 基础模板;查询词超过 8 条 → 硬截断(避免 SerpAPI 调用过多);整阶段异常 → also 回退模板并记录错误。

### 阶段 2:搜索(collect_search_results_detail)— SerpAPI + 按 link 去重

**做什么**:照策略中的查询词逐个调 SerpAPI(Google 搜索),把所有结果按 `link` 去重汇总。

**实现技术**:
- **SerpAPI Python SDK**(`serpapi.GoogleSearch`),见 [tools/search_tools.py:11-47](../backend/app/tools/search_tools.py#L11-L47)。固定参数 `engine=google`、`hl=zh-cn`、`gl=cn`,取 `organic_results` 的 title/link/snippet 三字段。
- **明细版方法** `_collect_search_results_detail`([search_agent.py:469-514](../backend/app/agents/search_agent.py#L469-L514)):除了去重汇总结果,还为每个查询词记录 `raw_count`/`new_count`/`error`/`samples`,供执行过程页展示"每查询词命中明细"。
- 用 `seen_links` set 按 URL 全局去重,避免同一招聘页被多个查询词重复带入。

### 阶段 3:梳理(extract_jobs)— LLM 分批提取岗位开放信息

**做什么**:把搜索结果交回 LLM,提取结构化招聘信息。**核心约束:`source_url` 必填**——没有可点击原始链接的结果一律不输出。

**实现技术**:
- **强约束系统提示词** `EXTRACT_SYSTEM_PROMPT`([search_agent.py:55-86](../backend/app/agents/search_agent.py#L55-L86)):定义了输出字段(job_title / is_open / source_platform / source_url / location / experience_years / education / salary_description / skills)与判断规则(过滤新闻/教程/已下线岗位;`source_url` 空则不输出;薪资技能只从 snippet 提取不臆造)。
- **分批处理** `EXTRACT_BATCH_SIZE = 8`([search_agent.py:520-587](../backend/app/agents/search_agent.py#L520-L587)):超过 8 条自动分批喂给 LLM。分批有两个目的——①避免单次输出被 `max_tokens` 截断;②降低中转站偶发"空 400"概率(单次请求越小越稳)。
- **截断检测** `_last_output_truncated`([search_agent.py:115-117](../backend/app/agents/search_agent.py#L115-L117)):记录每次调用 `finish_reason`,若为 `'length'` 标记本批被截断,结果可能不全。
- **跨批去重**:多批提取后按 `source_url` 再次去重,合并为最终列表。

### LLM 调用层:流式 + 指数退避重试

`_call_llm_with_retry`([search_agent.py:121-214](../backend/app/agents/search_agent.py#L121-L214))是所有 LLM 调用的统一入口,有两个关键的工程化设计:

1. **流式调用(`stream=True`)**:第三方 LLM 中转站偶发对非流式请求也回 `content-type: text/event-stream`,把 SSE 心跳 `: keepalive` 和行首空行漏进响应体,导致 SDK 按 JSON 解析失败。改用流式后 SDK 走 SSE 解码器,自动跳过空行与 `:` 注释行;同时流式天然更抗超时。
2. **重试机制**:对 `ValueError`(空内容)、`BadRequestError`(空 400)、`APIError`(5xx/网络)做指数退避重试(`delay` 从 2s 起步,每次 +2);但有明确错误 body 的 400(参数/鉴权问题)不重试。
3. **推理模型兼容**:检测 `delta.reasoning_content`(推理模型如 mimo-v2.5-pro 会先输出思考过程),记录 `has_reasoning=True`,避免把"模型还在想、content 暂为 null"误判为空响应而重试。阶段 3 的 `max_tokens=8192`(注释解释:3072 会被推理 eats 光,8192 实测能让 content 带完整 JSON 返回)。

---

## 三、核心功能二:任务执行可视化(steps_log 全链路追踪)

> 搜索到底卡在哪一步?LLM 给出的策略是否合理?SerpAPI 每条查询词命中多少?这些疑问都能在「执行过程」页逐步复盘。
> 实现文件:[backend/app/services/search_service.py](../backend/app/services/search_service.py) + [frontend/src/views/ExecutionDetail.vue](../frontend/src/views/ExecutionDetail.vue)

### 后端:分阶段写进度 + 中间数据落库

`SearchService._execute_task`([search_service.py:59-214](../backend/app/services/search_service.py#L59-L214))在三个阶段前后各调用 `_update_progress`,把当前阶段 `current_step`、进度百分比、信息写入 `SearchTask` 记录,并 **立即 commit**,供前端轮询。

`_update_progress` → `_append_step`([search_service.py:218-263](../backend/app/services/search_service.py#L218-L263))向 `steps_log` 字段(JSON 数组)追加一条记录,关键设计是每条记录可携带 `detail` 字段,**原样存进中间执行数据**,包括:

- **planning 阶段**:`plan_queries`、`target_platforms`、`include_keywords`、`exclude_keywords`、`rationale`、`llm_raw_output`(LLM 原始输出,限长 4000 字符防爆)、`system_prompt`、`user_message`
- **searching 阶段**:`total_results`、`queries_count`、`queries_detail`(每查询词命中数/样例/错误)
- **extracting 阶段**:`extracted_count`、`batch_count`、`batches`(各批 input_count/output_count/finish_reason/truncated/raw_output/user_message)
- **done 阶段**:`saved`/`duplicated`/`skipped_no_url`/`failed` 统计

`steps_log` 存在 `SearchTask.steps_log`(`Text` 列)中,[models/job.py:43](../backend/app/models/job.py#L43)。

### 前端:按 phase 分组可视化 + 3 秒轮询

[ExecutionDetail.vue](../frontend/src/views/ExecutionDetail.vue) 是执行过程页:
- 进入时从 URL `?ids=` 拿待观察的 task_ids(由仪表盘触发搜索后跳转带上);无 ids 则展示最近 10 条任务。
- **3 秒轮询**([ExecutionDetail.vue:47-61](../frontend/src/views/ExecutionDetail.vue#L47-61)):所有任务进入终态(completed/failed)后停止轮询。
- **按 phase 分组** `groupPhases`([ExecutionDetail.vue:85-104](../frontend/src/views/ExecutionDetail.vue#L85-L104)):把 `steps_log` 按 planning/searching/extracting/done 归类为四个可折叠块,每个块带 emoji 图标(🧠/🔍/📊/✅)和标题(如"阶段1 · AI 规划搜索策略")。
- `getDetail` / `d()` 安全访问 detail 字段(避免 Vue 模板里 `?.` 编译不稳定)。
- 展开任一块可看到该阶段喂给 LLM 的完整提示词、LLM 原始输出、搜索命中明细等。

### 两段式执行:预创建 + 后台异步

任务执行采用"预创建 + 后台异步"模式([search_service.py:305-357](../backend/app/services/search_service.py#L305-L357)):
1. `prepare_batch_tasks`:主请求里预创建所有 `SearchTask` 记录(status=planning)并 commit,立即返回 task_ids。
2. `run_existing_tasks`:后台线程逐个执行,每个任务独立 try/except,单失败不影响其他。

这样前端触发搜索后能**立刻拿到 task_ids 开始轮询可视化**,不必等整个流水线跑完。[api/tasks.py:43-92](../backend/app/api/tasks.py#L43-L92) 用 FastAPI `BackgroundTasks` 把 `run_search_background` 丢进线程池。

### 僵尸任务兜底

进程重启会留下 running/planning 状态的"僵尸"任务。三层兜底保证不留僵尸:
1. **启动时清理** `_cleanup_zombie_tasks`([main.py:49-66](../backend/app/main.py#L49-L66)):把 running/planning/searching/extracting 状态全标 failed。
2. **任务级兜底** `_execute_task` 整体 try/except + `_mark_task_failed`([search_service.py:359-370](../backend/app/services/search_service.py#L359-L370))。
3. **后台函数级兜底** `run_search_background`([api/tasks.py:18-40](../backend/app/api/tasks.py#L18-L40))最后再扫一次 running 标 failed。
4. **定时任务级兜底**([scheduler/__init__.py:54-65](../backend/app/scheduler/__init__.py#L54-L65))。

---

## 四、核心功能三:公司 × 职位监测清单管理

> 系统以「公司 × 职位」笛卡尔积作为监测单元,这是最少必要信息的监测清单。
> 实现文件:[api/companies.py](../backend/app/api/companies.py) + [api/positions.py](../backend/app/api/positions.py) + [models/company.py](../backend/app/models/company.py) + [models/position.py](../backend/app/models/position.py)

### 数据模型(公司)

`Company`([models/company.py:16-60](../backend/app/models/company.py#L16-L60))字段:`name`、`aliases`(JSON 文本,别名列表)、`website`、`career_page`(招聘页)、`industry`、`notes`、`is_active`(启用开关)。`aliases` 用 `Text` 列存 JSON 字符串,`to_dict` 时反序列化为 list——这是 SQLite 不支持原生数组列的通用做法,贯穿所有模型。

### 数据模型(职位)

`PositionConfig`([models/position.py:16-69](../backend/app/models/position.py#L16-L69))字段:`title`、`keywords`(JSON)、`exclude_keywords`(JSON)、`locations`(目标城市 JSON)、`experience_level`(junior/mid/senior)、`is_active`。

### API 技术

- **FastAPI 路由 + Pydantic 校验**:[schemas/company.py](../backend/app/schemas/company.py) / [schemas/position.py](../backend/app/schemas/position.py) 定义 `CompanyCreate`/`CompanyUpdate`/`CompanyResponse` 等,带字段校验。
- **增删改查 + 软删除/启用**:`GET / /api/companies/`(带分页/筛选/关键字)、`POST`、`PUT`、`DELETE`(软删除即置 `is_active=false`)、`PATCH .../enable`(重新启用)、`DELETE .../hard`(物理删除)。前端 [api/index.ts](../frontend/src/api/index.ts) 封装为 `companyApi`/`positionApi` 对象。
- **SQLAlchemy 2.0 ORM**:`db.query(Company).filter(...).all()`,`ilike` 模糊匹配公司名/行业。

### 前端管理页面

- [CompanyManage.vue](../frontend/src/views/CompanyManage.vue):Element Plus `el-table` + `el-dialog` 表单,支持搜索关键字筛选、启用/禁用切换、软删除/彻底删除。
- [PositionConfig.vue](../frontend/src/views/PositionConfig.vue):同样模式,关键词/排除词/城市用动态 tag 输入。

---

## 五、核心功能四:招聘信息检索与去重入库

> 阶段 3 提取出的招聘信息,如何清洗、去重、入库、检索。
> 实现文件:[api/jobs.py](../backend/app/api/jobs.py) + [search_service._save_jobs](../backend/app/services/search_service.py#L390-L497)

### 数据模型

`JobListing`([models/job.py:80-171](../backend/app/models/job.py#L80-L171))字段丰富:`job_title`、`is_open`(true/false/unknown 字符串,核心监测信号)、`salary_min/max/description`、`location`、`experience_years`、`education`、`skills`(JSON)、`job_description`/`requirements`/`benefits`、`source_platform`、`source_url`(必填)、`source_id`(去重用)、`published_at`/`crawled_at`、`is_duplicate`/`is_verified`。

### 入库清洗(_save_jobs)

[search_service.py:390-497](../backend/app/services/search_service.py#L390-L497) 对每条 LLM 提取结果做清洗:
- **链接必填兜底**:`source_url` 为空一律 `skipped_no_url` 跳过。
- **is_open 归一**:bool → "true"/"false" 字符串;非合法值 → "unknown"。
- **薪资解析** `_parse_salary`:正则提取首个数字为整数月薪;"面议"/"negotiable" → None。
- **source_id 生成** `_generate_source_id`:`source_url` 的 MD5(稳定去重键);无 url 则用"标题+公司名"MD5。
- **去重逻辑**:`(source_platform, source_id)` 复合键查 existing——存在则更新字段(information 最新),不存在则新建。返回 `{saved, duplicated, skipped_no_url, failed}` 统计。

### 检索 API

`GET /api/jobs/`([api/jobs.py:144-219](../backend/app/api/jobs.py#L144-L219))支持多条件筛选:`company_id`、`keyword`(在 job_title/job_description/skills 文本里 `ilike`)、`location`、`salary_min/max`、`source_platform`、`is_verified`;排除 `is_duplicate`;分页;按 `crawled_at desc` 排序。

**join 取公司名**:`db.query(JobListing).join(Company, ...).add_columns(Company.name.label("company_name"))`,让每条岗位带着公司名返回,前端无需二次查询。

### 前端检索页

[JobList.vue](../frontend/src/views/JobList.vue)(530 行):顶部筛选表单 + 分页表格 + 状态筛选(`is_open` 用 tag 颜色区分 true/false/unknown)+ 详情抽屉,`source_url` 渲染为可点击外链。

---

## 六、核心功能五:基于 APScheduler 的定时任务调度

> 按 cron 表达式定期执行「全部启用公司 × 启用职位」的批量搜索,支持运行时热更新。
> 实现文件:[scheduler/__init__.py](../backend/app/scheduler/__init__.py)

### 单例调度器 + 线程锁

- 进程内唯一 `BackgroundScheduler`([scheduler/__init__.py:75-85](../backend/app/scheduler/__init__.py#L75-L85)),时区硬编码 `Asia/Shanghai`,与数据库时间戳时区一致。
- `threading.Lock` 保护 `init`/`reschedule`/`shutdown` 不并发踩踏。
- 固定 `job_id = "scheduled_batch_search"`,`replace_existing=True`,便于 reschedule 定位。

### cron 触发 + 容错策略

`_apply_job`([scheduler/__init__.py:87-112](../backend/app/scheduler/__init__.py#L87-L112)):
- `CronTrigger.from_crontab(settings.SCHEDULE_CRON)` 解析标准 5 段 cron。
- `misfire_grace_time=3600`:错过触发容忍 1 小时(进程重启后补跑)。
- `coalesce=True`:多次错过只补跑一次,避免堆积。
- `settings.SCHEDULE_ENABLED=False` 时不添加 job。

### 触发入口

`_run_scheduled_batch`([scheduler/__init__.py:32-67](../backend/app/scheduler/__init__.py#L32-L67))复用 `SearchService.prepare_batch_tasks + run_existing_tasks` 两段式流程,保证定时任务产出的 `SearchTask` 与手动触发同构,前端可视化和去重逻辑无需区分来源。带兜底:异常时扫一次 running 标 failed。

### 热更新 API

`PUT /api/schedules/current`([api/schedules.py:43-79](../backend/app/api/schedules.py#L43-L79)):
1. 先 `CronTrigger.from_crontab` 校验 cron 合法性,非法直接 400(避免保存了配置但调度器静默不生效)。
2. 修改内存 `settings.SCHEDULE_CRON` / `settings.SCHEDULE_ENABLED`。
3. 调 `reschedule()` 立即重排 job,无需重启进程。
4. 返回 `next_run_at`(下次执行 ISO 时间)。

> ⚠️ **已知局限**:当前修改仅改内存,重启后回退 `.env` 默认值(持久化写入 Schedule 表/`.env` 为待办项)。

### 前端 cron 友好配置

[utils/cronUtils.ts](../frontend/src/utils/cronUtils.ts) 实现 cron 表达式与友好配置(`ScheduleConfig`)的双向转换:
- `Frequency` 枚举:daily/every_n_hours/weekdays/weekly/every_n_minutes/custom。
- `toCron`:友好配置 → cron;`fromCron`:cron → 友好配置(回填 UI);`describeConfig`:转中文描述。
- [Settings.vue](../frontend/src/views/Settings.vue) 提供频率下拉 + 时间选择器 + 星期选择,实时预览 cron 与下次执行时间;高级模式可直接手填 cron。

---

## 七、核心功能六:多 LLM 服务兼容(OpenAI 兼容接口)

> 通过 OpenAI 兼容接口接入 OpenAI / Anthropic / Ollama / vLLM / 第三方代理 / Azure OpenAI。
> 实现文件:[core/config.py](../backend/app/core/config.py) + search_agent LLM 初始化

### 配置模型

`Settings`([core/config.py:17-127](../backend/app/core/config.py#L17-L127)) 用 **Pydantic Settings v2**(`pydantic-settings.BaseSettings`)从 `.env` 读取:
- `LLM_PROVIDER`(openai/anthropic/custom)、`LLM_API_BASE_URL`、`LLM_API_KEY`、`LLM_MODEL_NAME`、`LLM_USE_ANTHROPIC_FORMAT`。
- `@validator` 解析 `CORS_ORIGINS`(逗号分隔/JSON)、`EMAIL_TO_LIST`(逗号分隔/JSON)为 list。
- `get_llm_api_key()` 兼容旧 `ANTHROPIC_API_KEY`/`OPENAI_API_KEY`。

### 统一 OpenAI client

[search_agent.py:97-105](../backend/app/agents/search_agent.py#L97-L105) 用 `openai.OpenAI` 单一 client,通过 `base_url` 切换不同服务商——这是兼容多种 LLM 的关键:**只要服务暴露 OpenAI 兼容 `/v1/chat/completions` 接口即可接入**。`timeout=120s`、`max_retries=3`(SDK 层) + 应用层重试(见核心功能二)。

### 多种 .env 模板

项目提供 [`.env.example`](../backend/app/.env.example) / [`.env.ollama.example`](../backend/app/.env.ollama.example) / [`.env.vllm.example`](../backend/app/.env.vllm.example) / [`.env.proxy.example`](../backend/app/.env.proxy.example) 覆盖各场景,完整说明见 [docs/LLM_CONFIG.md](docs/LLM_CONFIG.md)。

### 诊断接口

- `GET /api/tasks/test-llm`([api/jobs.py:28-71](../backend/app/api/jobs.py#L28-L71)):用 `AsyncOpenAI` 发一条 "请回复'连接成功'" 验证连通,返回 llm_info + 响应。
- `GET /api/tasks/test-search`([api/jobs.py:74-139](../backend/app/api/jobs.py#L74-L139)):同步跑完整三阶段流水线(不写库),返回每步结果 + LLM 原始输出,用于定位卡在哪一步。

---

## 八、核心功能七:搜索完成邮件通知

> 每次手动或定时触发的批量搜索结束，自动汇总结果发送 HTML 邮件给配置的收件人，每次发送都有历史可查。
> 实现文件:[backend/app/services/email_service.py](../backend/app/services/email_service.py) + [backend/app/api/email.py](../backend/app/api/email.py) + [backend/app/api/email_logs.py](../backend/app/api/email_logs.py) + [backend/app/templates/email/search_report.html](../backend/app/templates/email/search_report.html) + [frontend/src/views/EmailLog.vue](../frontend/src/views/EmailLog.vue) + [frontend/src/views/ConfigTest.vue](../frontend/src/views/ConfigTest.vue)

### 邮件服务核心

`EmailService`([email_service.py:25-302](../backend/app/services/email_service.py#L25-L302)):

- **入口方法** `send_search_report(task_results)`([email_service.py:37-90](../backend/app/services/email_service.py#L37-L90)):接收本批次所有任务的执行结果 dict,统一返回 `{success, skipped, skip_reason, subject, recipients, error, duration_ms}` 的标准结果。
- **配置缺失兜底**:未配 `SMTP_USERNAME/PASSWORD` 或 `EMAIL_TO_LIST` → 直接 `skipped=True` 并写明原因,**不抛异常**,避免搜索任务主链路被邮件失败拖垮。
- **内容构建** `_build_email_content`([email_service.py:113-146](../backend/app/services/email_service.py#L113-L146)):统计 `total_tasks/completed_tasks/failed_tasks/total_jobs`,作为 Jinja2 模板上下文;主题格式 `[APP_NAME] 招聘信息搜索报告 - 发现 N 条新岗位`。
- **SMTP 发送** `_send_smtp`([email_service.py:179-189](../backend/app/services/email_service.py#L179-L189)):根据 `SMTP_PORT` 自动切换 SSL/STARTTLS(465 用 SSL,587 用 STARTTLS + starttls)。
- **异步封装** `_send_email`([email_service.py:148-177](../backend/app/services/email_service.py#L148-L177)):通过 `asyncio.get_event_loop().run_in_executor(...)` 把同步 smtplib 调用丢到线程池,在已有事件循环里不阻塞。
- **测试邮件** `send_test_email`([email_service.py:191-248](../backend/app/services/email_service.py#L191-L248)):复用真实报告模板渲染一份**示例报告**(`sample_results` 三条假任务),让收件人能预览实际收到邮件的样式,而不是收到一封"测试邮件"。

### HTML 邮件模板

`backend/app/templates/email/search_report.html` 用 Jinja2 渲染,展示:
- 报告时间(按 `CST` 时区格式化)。
- 汇总卡片:任务总数 / 完成数 / 失败数 / 新增岗位数。
- 逐条任务明细:公司名、职位、状态、jobs_found、错误信息(失败时)。

### EmailLog 历史落库

`record_email_log`([email_service.py:251-301](../backend/app/services/email_service.py#L251-L301))在每次发送尝试(成功/失败/跳过)后写一条 `EmailLog`:
- `trigger_type`:manual / scheduled(手动 or 定时)。
- `status`:success / failed / skipped。
- `subject / recipients / task_count / job_count / task_ids / error_message / duration_ms`:全部留痕。
- **写库失败也不抛异常**,只 `print` 日志,绝不阻塞搜索任务主流程。

### 触发点(已接入主链路)

邮件报告在两处自动触发:
1. **手动触发** `run_search_background`([api/tasks.py:46-75](../backend/app/api/tasks.py#L46-L75)):批量任务跑完后调用,`trigger_type="manual"`。
2. **定时触发** `_send_email_report`([scheduler/__init__.py:162-193](../backend/app/scheduler/__init__.py#L162-L193)):cron 触发的批量搜索完成后调用,`trigger_type="scheduled"`。

两处都用独立的 `SessionLocal` 起 session,主线程的 db 已关闭也不影响邮件落库。

### 配置查看 & 测试 API

- `GET /api/email/config`([api/email.py:35-49](../backend/app/api/email.py#L35-L49)):返回 SMTP 是否已配置 + host/port/username/recipient_count(密码不回显)。
- `POST /api/email/test`([api/email.py:52-81](../backend/app/api/email.py#L52-L81)):发一封示例报告邮件,验证 SMTP 链路与模板渲染。

### 邮件日志 API

- `GET /api/email-logs/`([api/email_logs.py:16-40](../backend/app/api/email_logs.py#L16-L40)):分页查询,可按 `status`(success/failed/skipped)、`trigger_type`(manual/scheduled)筛选,按创建时间倒序。
- `DELETE /api/email-logs/{id}`([api/email_logs.py:43-55](../backend/app/api/email_logs.py#L43-L55)):删除单条记录。

### 前端邮件相关页面

- [EmailLog.vue](../frontend/src/views/EmailLog.vue)(「邮件通知」):表格展示所有邮件发送记录,含状态 tag、主题、收件人、触发来源、耗时、错误信息(失败时展开);支持按状态/触发来源筛选。
- [ConfigTest.vue](../frontend/src/views/ConfigTest.vue)(「配置测试」):把 LLM / SerpAPI / SMTP 三类外部服务的连通性测试集中在一个页面(LLM 走 `/api/tasks/test-llm`、搜索流水线走 `/api/tasks/test-search`、SMTP 走 `/api/email/test`),让运维/排障时不必四处找接口。

---

## 九、核心功能八:仪表盘统计

> 一眼掌握监测规模与今日新增。
> 实现文件:[api/jobs.py:344-373](../backend/app/api/jobs.py#L344-L373) + [frontend/src/views/Dashboard.vue](../frontend/src/views/Dashboard.vue)

`GET /api/dashboard/stats` 返回四项:
- `company_count`:启用公司数。
- `job_count`:非重复招聘信息总数。
- `today_count`:今日新增(按北京时间 `CST` 算"今日"边界,与 `crawled_at` 时区一致)。
- `task_count`:任务总数。

[Dashboard.vue](../frontend/src/views/Dashboard.vue) 用 Element Plus 卡片展示统计 + 最近 5 条任务列表 + 「立即执行搜索」按钮(触发后跳转执行过程页带 `?ids=`)。

---

## 十、前端九大页面功能详解

前端技术栈:**Vue 3(`<script setup>`)+ Element Plus + Vue Router + Pinia + TypeScript + Vite**。auto-import(`unplugin-auto-import`)+ 组件自动注册(`unplugin-vue-components`)。端口 5173,Vite 配置 `/api` 代理到后端 8000。

| 路由 | 页面文件 | 功能 |
|------|---------|------|
| `/dashboard` | [Dashboard.vue](../frontend/src/views/Dashboard.vue) | 统计卡片 + 最近任务 + 立即执行搜索 |
| `/companies` | [CompanyManage.vue](../frontend/src/views/CompanyManage.vue) | 公司 CRUD + 启用/软删除/彻底删除 |
| `/positions` | [PositionConfig.vue](../frontend/src/views/PositionConfig.vue) | 职位配置 CRUD + 关键词/排除词/城市 tag 输入 |
| `/jobs` | [JobList.vue](../frontend/src/views/JobList.vue) | 招聘信息多条件筛选 + 分页 + 详情 + 外链 |
| `/tasks` | [TaskHistory.vue](../frontend/src/views/TaskHistory.vue) | 任务历史列表 + 状态筛选 + 跳执行过程 |
| `/executions` | [ExecutionDetail.vue](../frontend/src/views/ExecutionDetail.vue) | 单任务/多任务的三阶段执行可视化 + 3 秒轮询 |
| `/email-logs` | [EmailLog.vue](../frontend/src/views/EmailLog.vue) | 邮件发送历史 + 状态/触发来源筛选 + 错误信息展开 |
| `/settings` | [Settings.vue](../frontend/src/views/Settings.vue) | 定时任务友好配置(cron 双向转换)+ 启停 + 下次执行时间 |
| `/config-test` | [ConfigTest.vue](../frontend/src/views/ConfigTest.vue) | LLM / SerpAPI / SMTP 三类外部服务连通性测试 |

### axios 封装与拦截器

[api/index.ts](../frontend/src/api/index.ts):
- 创建 axios 实例,`baseURL` 从 `VITE_API_BASE_URL` 或默认 `http://localhost:8000`,`timeout=30000`。
- 响应拦截器统一 `return response.data`(调用方直接拿业务数据);错误拦截器用 `ElMessage.error` 弹错误(detail/message)。
- 各业务 API 封装为对象(`companyApi`/`positionApi`/`jobApi`/`taskApi`/`dashboardApi`/`scheduleApi`),类型化参数。

### 路由与守卫

[router/index.ts](../frontend/src/router/index.ts):7 条路由,根路径 redirect 到 dashboard;`beforeEach` 守卫设置 `document.title`;视图组件懒加载(动态 import)。

### 布局

[AppLayout.vue](../frontend/src/components/AppLayout.vue)(194 行):Element Plus 侧边栏菜单 + 顶栏,导航到七个页面。

---

## 十、部署与工程化

### 数据库与迁移

- **默认 SQLite**,零配置(`DATABASE_URL=sqlite:///./jobsentinel.db`);改一行可切 PostgreSQL/Supabase。
- **SQLAlchemy 2.0** ORM([models/database.py](../backend/app/models/database.py)):`create_engine` 带 `pool_pre_ping`(自动检测断连)、连接池配置;`SessionLocal` 工厂;`get_db` 依赖注入。
- **`init_db()`** [models/database.py:38-85](../backend/app/models/database.py#L38-L85):`Base.metadata.create_all` 自动建表 + 轻量手写迁移 `_migrate_search_task_columns`(用 `PRAGMA table_info` 检查列存在,缺失才 `ALTER TABLE ADD COLUMN`),解决 SQLite 不会因 ORM 新增字段自动加列的问题。
- 配置了 **Alembic**([alembic/](../backend/app/alembic/))但默认靠 `init_db()` 自动建表。

### 时区统一

全局统一东八区(`CST = timezone(timedelta(hours=8))`,[core/config.py:14](../backend/app/core/config.py#L14)):数据库时间戳、调度器时区、仪表盘"今日"边界全部用 CST;序列化带 `+08:00`,前端按浏览器本地时区换算。调度器写死 Asia/Shanghai 保证三方一致。

### Windows 兼容

[main.py:5-15](../backend/app/main.py#L5-L15) 把 stdout/stderr 强制 UTF-8,避免 Windows 中文控制台 GBK 编码遇 emoji 触发 `UnicodeEncodeError`。

### Docker 部署

- [backend/Dockerfile](../backend/app/../Dockerfile) + [docker-compose.yml](../docker-compose.yml):`docker-compose up --build` 一键起前后端。
- 生产建议:后端上 Railway,前端构建静态产物上 Vercel/Nginx,并调整 `CORS_ORIGINS` 与 `VITE_API_BASE_URL`。

---

## 附录:技术栈速查表

| 层 | 技术 | 用途 | 关键文件 |
|----|------|------|---------|
| 后端框架 | FastAPI 0.104 + Uvicorn 0.24 | 异步 Web 框架 / ASGI 服务器 | [main.py](../backend/app/main.py) |
| ORM | SQLAlchemy 2.0 | 数据建模 / 会话 | [models/](../backend/app/models/) |
| 数据校验 | Pydantic v2 + pydantic-settings | 请求响应模型 / 配置 | [schemas/](../backend/app/schemas/) [config.py](../backend/app/core/config.py) |
| 数据库 | SQLite(默认)/ PostgreSQL(可选) | 持久化 | [database.py](../backend/app/models/database.py) |
| 迁移 | Alembic + 手写 ALTER | 表结构变更 | [alembic/](../backend/app/alembic/) |
| LLM SDK | openai ≥1.6.1 + anthropic ≥0.18 | 多 LLM 兼容调用 | [search_agent.py](../backend/app/agents/search_agent.py) |
| 搜索 | serpapi / google-search-results | Google 搜索 | [search_tools.py](../backend/app/tools/search_tools.py) |
| 定时任务 | APScheduler 3.10 | cron 调度 / 热更新 | [scheduler/__init__.py](../backend/app/scheduler/__init__.py) |
| 前端框架 | Vue 3.3(`<script setup>`) | 响应式 UI | [src/](../frontend/src/) |
| UI 库 | Element Plus 2.4 | 组件库 | 各 views |
| 路由/状态 | Vue Router 4 + Pinia 2 | 路由 / 全局状态 | [router/](../frontend/src/router/) |
| 语言/构建 | TypeScript 5.3 + Vite 5 | 类型 + 打包 | [vite.config.ts](../frontend/vite.config.ts) |
| HTTP | axios 1.6 | 前端请求 | [api/index.ts](../frontend/src/api/index.ts) |
| 部署 | Docker + docker-compose | 容器化 | [docker-compose.yml](../docker-compose.yml) |
| 邮件 | aiosmtplib + jinja2 + EmailLog | 搜索完成报告 / 历史追溯 | [email_service.py](../backend/app/services/email_service.py) |

---

## 附:已知待完善项(来自 README 路线图)

- 定时配置持久化:修改需写入 Schedule 表/`.env`,当前仅内存。
- 招聘信息导出:CSV / Excel。
- API 鉴权、CORS 收敛、请求限流。
- 搜索结果去重 / 薪资标准化 / 技能标签自动提取等数据质量优化。
