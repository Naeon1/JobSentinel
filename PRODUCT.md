# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

已有现成代码库回答此问题，无需询问：

- 后端：FastAPI · Uvicorn · SQLAlchemy 2.0 · Pydantic v2 · APScheduler · OpenAI/Anthropic SDK · SerpAPI
- 前端：Vue 3 · Element Plus · Vue Router · Pinia · TypeScript · Vite
- 数据库：SQLite（默认，零配置）/ PostgreSQL（可选）
- 部署：Docker · docker-compose

## Users

主要用户是**求职者（自托管）**。他们自行部署 JobSentinel，维护一份「目标公司 × 目标职位」的监测清单，用于在求职期间第一时间发现目标公司的新投递入口，拿到可点击的原始招聘链接。使用场景偏个人/小范围自托管，通常单用户操作。

## Product Purpose

JobSentinel 是基于 AI 的招聘信息自动搜索与监测系统。它让大模型主导搜索策略：把「公司 + 职位」信息交给 LLM 规划结构化查询词（含 `site:` 限定覆盖官方招聘页），调用 SerpAPI 搜索，再由 LLM 从结果中提取结构化在招岗位信息（含**必填的原始链接**），统一入库供筛选、查看与跟踪。成功意味着用户无需手动反复刷招聘页，系统会按 cron 定时或手动触发自动监测，把新开放的投递入口第一时间汇总到面前。

## Positioning

差异化定位是两点结合：

1. **LLM 主导搜索策略**——大模型根据公司/职位信息动态规划查询词、目标平台、关键词与排除词，而非硬编码查询模板；邻居产品多停留在固定模板或纯关键词匹配。
2. **投递入口第一时间发现**——定位是监测/告警系统，目标是让用户抢在岗位刚开放时拿到可点击的原始投递链接，而非做一个招聘信息聚合门户。

## Operating Context

- 用户在求职期间持续使用：配置公司清单（名称/别名/官网/招聘页/行业）、职位清单（职位名/关键词/排除词/目标城市/经验级别），随后主要靠定时任务自动跑。
- 三阶段搜索流水线：规划（LLM 输出查询策略）→ 搜索（SerpAPI 调 Google，按链接去重）→ 梳理（LLM 分批提取结构化在招信息，`source_url` 必填）。
- 需要外部依赖：一个 SerpAPI Key + 一个 LLM API Key（通过 OpenAI 兼容接口接入 OpenAI/Anthropic/Ollama/vLLM/第三方代理/Azure OpenAI）。
- 默认 SQLite 零配置启动，本地即可运行；进程重启自动清理僵尸任务。
- 前端 7 个页面：仪表盘 / 公司管理 / 职位配置 / 招聘信息 / 任务历史 / 执行过程 / 系统设置。
- 每个搜索任务的分阶段进度、提示词、LLM 原始输出、每查询词命中明细都写入 `steps_log`，供「执行过程」页逐步复盘，定位搜索卡在哪一步。

## Capabilities and Constraints

**已实现功能：**

- 后端 5 个 API 模块（companies / positions / jobs / tasks / schedules）+ 三阶段搜索 Agent + 定时任务调度器 + 仪表盘统计。
- 定时任务调度：基于 APScheduler `BackgroundScheduler`，cron 表达式定期执行「全部启用公司 × 启用职位」批量搜索；支持 cron 合法性校验与运行时热更新（无需重启进程）；`misfire_grace_time=3600`、`coalesce=True`。
- 任务执行可视化：`steps_log` 全链路追踪（规划策略/搜索命中/LLM 提取结果）。
- 多 LLM 兼容：OpenAI 兼容接口 + 流式调用 + 指数退避重试。
- 诊断接口：`test-llm` 验证 LLM 连通、`test-search` 同步跑完整流水线不写库。

**已知约束/待完善（明确未决）：**

- 邮件服务：依赖已列入 `requirements.txt`，但发送逻辑待实现（搜索完成后汇总新增招聘数发送到 `EMAIL_TO_LIST`）。
- 定时任务配置持久化：当前「系统设置」页修改仅改内存，重启后回退默认值（需写入 Schedule 表或 `.env`）。
- 招聘信息导出（CSV / Excel）待实现。
- API 鉴权、CORS 收敛、请求限流等安全加固待完善。
- 搜索结果去重 / 薪资标准化 / 技能标签自动提取等数据质量优化待完善。

**术语：**「公司 × 职位」监测清单、三阶段搜索流水线（规划/搜索/梳理）、`steps_log`、`source_url` 必填。

## Brand Commitments

- 项目名：**JobSentinel**（Sentinel 取「哨兵/监测」之意，呼应「监测招聘开放情况」定位）。
- 开源项目，MIT License，© 2026 JobSentinel Contributors。
- 现有文案以简体中文为主（README、docs 均为中文）。
- 运营形态（纯自托管 vs 未来 SaaS）与品牌视觉资产未定，暂不约束。

## Evidence on Hand

- 真实代码：[backend/app/](backend/app/)（分层 api → services → agents → tools → models → schemas → scheduler → core）。
- 文档：[README.md](README.md)、[docs/FEATURES.md](docs/FEATURES.md)（功能拆解+技术细节）、[docs/PROGRESS.md](docs/PROGRESS.md)（开发进度）、[docs/LLM_CONFIG.md](docs/LLM_CONFIG.md)（大模型配置）。
- 数据模型：Company / PositionConfig / SearchTask / JobListing / Schedule。
- 缺席项：无真实客户证言、无 benchmark 数据、无部署案例；未来视觉/营销工作不得伪造此类内容。

## Product Principles

1. **LLM 主导，而非模板堆砌**——搜索策略由大模型动态规划，让 AI 真正承担策略制定，硬编码只作兜底。
2. **原始链接是一等公民**——`source_url` 必填，没有可点击原始投递入口的结果不输出，拒绝无来源的岗位摘要。
3. **可复盘的执行透明度**——每个任务全链路 `steps_log` 可追溯，让用户能定位搜索到底卡在哪一步，而非黑盒。
4. **自托管、零配置起步**——默认 SQLite、开箱即用，求职者本地即可跑起来；重型数据库与部署是可选增强。
5. **监测优先于聚合**——产品目标是「第一时间发现新投递入口」的哨兵，不是做又一个招聘信息门户。

## Accessibility & Inclusion

当前未确立产品特定的无障碍标准；前端基于 Element Plus，后续视觉工作应遵循常规 web 可访问性实践（键盘可达、对比度、语义化）。具体标准待用户明确后补充。
