"""
招聘信息搜索Agent（LLM 主导三阶段流水线）

流水线：
  阶段1 规划：把公司+职位信息交给 LLM，输出结构化搜索策略（查询词、目标平台、关键词等）
  阶段2 搜索：用策略中的查询词调用 SerpAPI 搜索并去重
  阶段3 梳理：把搜索结果交回 LLM 提取岗位开放信息（重点：是否在招 + 原始链接必填）

相比早期的硬编码查询词模板，这个方案让 LLM 真正主导搜索策略，更贴合"监测岗位开放情况"的目标。
全链路同步，放进 BackgroundTask 由 FastAPI 线程池执行；LLM 使用原生 openai 同步 client，
兼容第三方 API（与 test-llm 接口相同的调用方式）。
"""

import json
import re
from typing import List, Dict, Any, Optional, Tuple

from app.core.config import settings
from app.tools.search_tools import serpapi_search


# ==================== 阶段1：规划提示词 ====================

PLAN_SYSTEM_PROMPT = """你是一个资深的招聘信息搜索策略专家。你的任务是根据给定的公司信息和职位信息，制定一套结构化的搜索引擎搜索策略，用于监测该公司该岗位的招聘开放情况。

## 目标
帮用户**监测目标公司、目标职位是否在招人**，第一时间发现新的招聘投放入口。重点是"有没有在招、在哪儿招、原帖在哪"，而不是抠薪资细节。

## 输入
你会收到公司信息（名称、别名、官网、招聘页、行业）和职位信息（职位名、关键词、排除词、目标城市、经验级别）。

## 任务
综合公司特点与职位特点，设计 3-8 条 Google 搜索查询词，并标注预期命中的招聘平台。可灵活使用：
- 公司名 + 职位名 + "招聘"
- 公司名 + 职位名 + 平站站点限定（如 `site:zhipin.com`、`site:liepin.com`、`site:linkedin.com`、`site:nowcoder.com`）
- 公司名 + 招聘官网（如公司有 career_page 可专门搜其官方招聘页）
- 按目标城市细化

## 输出格式
严格输出 JSON 对象，不要有任何其他文字、解释或 markdown 代码块标记。**JSON 的键名必须用下面指定的英文键名**，禁止用中文键名（如写"查询""理由"会导致解析丢失，等同失败）。直接以 { 开头。字段：
{
  "queries": ["查询词1", "查询词2", ...],
  "target_platforms": ["预计命中的平台，如 公司官网、Boss直聘、猎聘、领英、智联等招聘平台"],
  "include_keywords": ["应重点关注的关键词"],
  "exclude_keywords": ["应排除的干扰词，如新闻、舆情"],
  "rationale": "一句话说明这套策略的思路（中文）"
}

示例：
{"queries":["字节跳动 Python 招聘","字节跳动 Python site:zhipin.com","字节跳动 工程师 site:jobs.bytedance.com"],"target_platforms":["Boss直聘","字节跳动官网"],"include_keywords":["Python","后端"],"exclude_keywords":["新闻","舆情"],"rationale":"官网+主流平台双覆盖，官网岗最准"}"""


# ==================== 阶段3：梳理提示词 ====================

EXTRACT_SYSTEM_PROMPT = """你是一个专业的招聘信息分析专家。你的任务是从搜索引擎结果中识别该公司该岗位的**招聘开放情况**，提取结构化信息供用户查看原文投递。

## 核心目标
监测"目标公司、目标职位目前是否在招人"，并给出可点击的原始链接让用户去核实和投递。**原始链接 source_url 是必填的**——没有可点击原始链接的结果一律不输出。

## 输入
一批搜索引擎结果，每条含 title、link、snippet，来自对某公司某职位的招聘搜索。

## 任务：输出字段（精简，只求"在不在招 + 在哪儿 + 原文链接"）
- job_title: 职位名称
- is_open: 是否在招（true=有明确招聘入口/在招 / false=疑似停招或过期 / unknown=不确定），默认 unknown
- source_platform: 来源平台（据 link 域名判断，如 Boss直聘、猎聘、领英、公司官网、智联、牛客）
- source_url: **必填，该条结果的 link，必须是可点击的原始链接**
- location: 工作地点
- experience_years: 经验要求（如 "3-5年"，无法判断则 null）
- education: 学历
- salary_description: 薪资原始描述（如 "40-60K" 或 "25-35K·15薪"，无法判断则 null）
- skills: 技能列表（仅从 snippet 可见文字中提取，摘要有限故结果天然不完整，不可臆造）

## 判断规则
- 只提取与目标公司、目标职位相关的真实招聘信息
- 过滤掉新闻报道、爬虫教程、个人博客、公司介绍页（非具体岗位）、舆情、已下线岗位等
- snippet 中明确出现"已下线/已关闭/过期/停止招聘" → is_open=false
- 多条结果指向同一 source_url 的合并为一条，取信息最完整的
- **source_url 为空则该条一律不输出**
- 薪资、技能只从 snippet 提取确凿信息，不可臆造

## 输出格式
严格输出 JSON 数组，直接以 [ 开头、] 结尾，不要任何其他文字或 markdown 代码块标记。没有有效信息则输出 []。**若有多条符合条件的结果，全部输出，不要只挑一条。**

示例（含多条）：
[{"job_title":"Python后端开发工程师","is_open":true,"source_platform":"Boss直聘","source_url":"https://www.zhipin.com/job/xxx","location":"上海","experience_years":"3-5年","education":"本科","salary_description":"40-60K","skills":["Python","MySQL"]},{"job_title":"Python Developer","is_open":true,"source_platform":"LinkedIn","source_url":"https://www.linkedin.com/jobs/view/xxx","location":"Beijing","experience_years":"5-10年","education":"硕士","salary_description":null,"skills":["Python","AWS"]}]"""


class SearchAgent:
    """招聘信息搜索Agent（LLM 主导三阶段，全同步执行）

    阶段1 plan_search：LLM 输出结构化搜索策略
    阶段2 搜索：SerpAPI 照策略查询并按 link 去重
    阶段3 extract_jobs：LLM 提取岗位开放信息（source_url 必填）
    """

    def __init__(self):
        from openai import OpenAI

        self.client = OpenAI(
            api_key=settings.get_llm_api_key(),
            base_url=settings.LLM_API_BASE_URL,
            timeout=120.0,
            max_retries=3,
        )
        self.model_name = settings.LLM_MODEL_NAME
        self.last_raw_output = ""  # 最近一次阶段3 本批 LLM 原始输出
        self.last_plan_output = ""  # 最近一次阶段1 LLM 原始输出，用于诊断
        self.last_plan_user_message = ""  # 阶段1 喂给 LLM 的 user message（可视化）
        self.last_plan_system_prompt = ""  # 阶段1 系统提示词（可视化）
        self.last_extract_system_prompt = ""  # 阶段3 系统提示词（可视化）
        self.last_extract_batches: List[Dict[str, Any]] = []  # 阶段3 各批明细
        self._last_finish_reason: Optional[str] = None  # 最近一次流式调用的结束原因

    def _last_output_truncated(self) -> bool:
        """最近一次 LLM 调用是否因 max_tokens 截断（finish_reason == 'length'）。"""
        return self._last_finish_reason == "length"

    # ==================== LLM 调用（带重试） ====================

    def _call_llm_with_retry(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: int = 4096,
        retries: int = 4,
    ) -> str:
        """
        流式调用 LLM 并对瞬时故障做指数退避重试。

        为什么用流式：第三方 LLM 中转站（如 mimo-v）偶发对非流式请求也回
        `content-type: text/event-stream`，把 SSE 心跳 `: keepalive` 和行首空行
        漏进响应体，导致 openai SDK 按 JSON 解析失败、把整个响应体当 str 返回。
        改用 stream=True 后 SDK 走 SSE 解码器，自动跳过空行与 `:` 注释行，
        心跳不再污染正文。同时 stream 天然更抗超时，长输出场景更稳。

        重试仍保留，兜真正的网络层/5xx 故障。对"非标准响应"（拼接后为空、
        或仍含未消化心跳）也重试。
        """
        import time
        from openai import BadRequestError, APIError

        delay = 2
        last_err: Optional[Exception] = None
        for attempt in range(retries + 1):
            try:
                stream = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=0,
                    max_tokens=max_tokens,
                    stream=True,
                )
                parts: List[str] = []
                finish_reason: Optional[str] = None
                has_reasoning = False  # 是否出现过 reasoning_content（推理模型）
                for chunk in stream:
                    choices = getattr(chunk, "choices", None)
                    if not choices:
                        continue
                    delta = choices[0].delta
                    content = getattr(delta, "content", None)
                    if content:
                        parts.append(content)
                    # 推理模型会先把思考写在 reasoning_content，content 此时为 null；
                    # 这并非流异常，只是模型还在"想"。记录发生过，避免误判空响应。
                    reasoning = getattr(delta, "reasoning_content", None)
                    if reasoning:
                        has_reasoning = True
                    if choices[0].finish_reason:
                        finish_reason = choices[0].finish_reason
                output = "".join(parts)
                # 只有"既没 content 也没 reasoning"才视为空响应。
                # 推理模型 reasoning 写满 max_tokens、content 还没开始时，output 会空
                # 但 has_reasoning=True → 真正的失败应由调用方按 finish_reason 截断判断，
                # 这里不重试（重试同样会被 reasoning 吃光）。
                if not output and not has_reasoning:
                    raise ValueError("LLM 流式返回空内容（疑似瞬时故障）")
                self._last_finish_reason = finish_reason
                return output
            except ValueError as e:
                last_err = e
                if attempt < retries:
                    print(f"[SearchAgent] LLM 返回空内容，{delay}s 后重试 (第{attempt + 1}/{retries} 次)")
                    time.sleep(delay)
                    delay += 2
                    continue
                raise
            except BadRequestError as e:
                last_err = e
                body = ""
                try:
                    body = e.response.text if e.response is not None else ""
                except Exception:
                    body = ""
                if body:
                    # 有明确错误 body，说明是参数/鉴权问题，重试无意义
                    raise
                if attempt < retries:
                    print(f"[SearchAgent] LLM 返回空 400（疑似瞬时故障），{delay}s 后重试 (第{attempt + 1}/{retries} 次)")
                    time.sleep(delay)
                    delay += 2
                    continue
                raise
            except APIError as e:
                last_err = e
                if attempt < retries:
                    print(f"[SearchAgent] LLM 调用异常 {type(e).__name__}，{delay}s 后重试 (第{attempt + 1}/{retries} 次)")
                    time.sleep(delay)
                    delay += 2
                    continue
                raise
        if last_err:
            raise last_err
        return ""

    # ==================== 编排入口 ====================

    def search_company_jobs(
        self,
        company: Dict[str, Any],
        position: Dict[str, Any],
        max_results: int = 10,
    ) -> Dict[str, Any]:
        """
        执行完整三阶段流水线（同步）。

        Args:
            company: 公司信息 dict（name/aliases/website/career_page/industry）
            position: 职位信息 dict（title/keywords/exclude_keywords/locations/experience_level）
            max_results: 每个查询词的最大结果数

        Returns:
            {
                "plan": {...},                  # 阶段1 输出的搜索策略
                "search_results_count": int,     # 阶段2 汇总去重后的结果数
                "jobs": [...]                    # 阶段3 提取的招聘信息（每条 source_url 非空）
            }
        """
        company_name = company.get("name", "")
        position_title = position.get("title", "")
        print(f"[SearchAgent] 开始搜索: company={company_name}, position={position_title}")

        # 阶段1：规划
        plan = self.plan_search(company, position)
        if not plan or not plan.get("queries"):
            print("[SearchAgent] 阶段1 未产出有效策略")
            return {"plan": plan, "search_results_count": 0, "jobs": []}

        print(f"[SearchAgent] 阶段1 策略: {len(plan.get('queries', []))} 条查询词")

        # 阶段2：搜索
        all_results = self._collect_search_results(plan.get("queries", []), max_results)
        print(f"[SearchAgent] 阶段2 汇总搜索结果: {len(all_results)} 条")

        if not all_results:
            return {"plan": plan, "search_results_count": 0, "jobs": []}

        # 阶段3：梳理
        jobs = self.extract_jobs(company_name, position_title, all_results)
        print(f"[SearchAgent] 阶段3 提取招聘信息: {len(jobs)} 条")

        return {
            "plan": plan,
            "search_results_count": len(all_results),
            "jobs": jobs,
        }

    # ==================== 阶段1：规划 ====================

    def plan_search(
        self,
        company: Dict[str, Any],
        position: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        阶段1：把公司+职位信息交给 LLM，输出结构化搜索策略（同步，一次 LLM 调用）。

        Returns:
            搜索策略 dict（queries/target_platforms/include_keywords/
            exclude_keywords/rationale）。失败返回 {}。
        """
        user_message = self._build_plan_user_message(company, position)
        self.last_plan_user_message = user_message
        self.last_plan_system_prompt = PLAN_SYSTEM_PROMPT

        try:
            output = self._call_llm_with_retry(
                messages=[
                    {"role": "system", "content": PLAN_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=4096,
            )
            self.last_plan_output = output
            print(f"[SearchAgent] 阶段1 LLM输出长度: {len(output)}")

            plan = self._parse_plan_output(output)
            # 兜底：若 LLM 没给 queries，退回基础模板
            if not plan or not plan.get("queries"):
                plan = {
                    "queries": self._fallback_queries(company, position),
                    "target_platforms": [],
                    "include_keywords": [],
                    "exclude_keywords": [],
                    "rationale": "LLM 未产出有效策略，使用基础查询词模板",
                }
            # 硬截断：最多 8 条查询词，避免 SerpAPI 调用过多
            MAX_QUERIES = 8
            if len(plan["queries"]) > MAX_QUERIES:
                print(f"[SearchAgent] 查询词 {len(plan['queries'])} 条超过上限，截断为 {MAX_QUERIES} 条")
                plan["queries"] = plan["queries"][:MAX_QUERIES]
            return plan

        except Exception as e:
            print(f"[SearchAgent] 阶段1 规划失败: {e}")
            self.last_plan_output = f"[LLM_CALL_ERROR] {type(e).__name__}: {e}"
            return {
                "queries": self._fallback_queries(company, position),
                "target_platforms": [],
                "include_keywords": [],
                "exclude_keywords": [],
                "rationale": f"规划失败，使用基础模板: {e}",
            }

    def _build_plan_user_message(
        self,
        company: Dict[str, Any],
        position: Dict[str, Any],
    ) -> str:
        """构造阶段1 的用户消息（公司+职位信息）"""
        website = company.get("website") or ""
        career_page = company.get("career_page") or ""

        # 从官网 URL 提取主域名（如 https://www.alibaba.com → alibaba.com）
        import re as _re
        website_domain = ""
        if website:
            m = _re.search(r"https?://(?:www\.)?([^/]+)", website)
            if m:
                website_domain = m.group(1)

        company_info = {
            "name": company.get("name", ""),
            "aliases": company.get("aliases", []),
            "website": website,
            "career_page": career_page,
            "industry": company.get("industry"),
        }
        position_info = {
            "title": position.get("title", ""),
            "keywords": position.get("keywords", []),
            "exclude_keywords": position.get("exclude_keywords", []),
            "locations": position.get("locations", []),
            "experience_level": position.get("experience_level"),
        }

        hints = []
        if website_domain:
            hints.append(f"- 公司官网域名为 {website_domain}，**必须**包含至少一条 `site:{website_domain}` 查询以覆盖公司自有招聘页面")
        if career_page:
            hints.append(f"- 公司招聘页为 {career_page}，**必须**包含一条 `site:` 查询指向该地址（如有独立域名）或直接在查询词中引用")
        if not website and not career_page:
            hints.append("- 公司未提供官网/招聘页信息，请尝试通过搜索引擎查询该公司官网并在查询词中使用 `site:` 限定")

        hint_block = ""
        if hints:
            hint_block = "\n\n## 特别要求\n" + "\n".join(hints)

        return f"""请为以下公司与职位制定搜索策略。

公司信息：
{json.dumps(company_info, ensure_ascii=False, indent=2)}

职位信息：
{json.dumps(position_info, ensure_ascii=False, indent=2)}

请输出结构化搜索策略 JSON。{hint_block}"""

    def _fallback_queries(
        self,
        company: Dict[str, Any],
        position: Dict[str, Any],
    ) -> List[str]:
        name = company.get("name", "")
        title = position.get("title", "")
        locations = position.get("locations") or []
        queries = [
            f"{name} {title} 招聘",
            f"{name} 社招 {title}",
            f"{name} {title} boss直聘",
        ]
        for loc in locations[:2]:
            queries.append(f"{name} {title} {loc} 招聘")
        return queries

    def _parse_plan_output(self, output: str) -> Dict[str, Any]:
        """解析阶段1 的 JSON 对象输出，兼容 LLM 偶发回中文键名。"""
        if not output:
            return {}
        output = output.strip()
        # 去除可能的 markdown 代码块标记
        if output.startswith("```"):
            output = re.sub(r"^```(?:json)?\s*", "", output)
            output = re.sub(r"\s*```$", "", output)
            output = output.strip()

        obj: Optional[Dict[str, Any]] = None
        try:
            if output.startswith("{"):
                obj = json.loads(output)
            else:
                match = re.search(r"\{[\s\S]*\}", output)
                if match:
                    obj = json.loads(match.group())
        except json.JSONDecodeError as e:
            print(f"[SearchAgent] 阶段1 JSON解析失败: {e}")
            print(f"[SearchAgent] 原始输出: {output[:500]}")
            return {}

        if not isinstance(obj, dict):
            return {}

        # 兼容中文键名：LLM 偶发不守英文键约束（如 "查询"/"理由"）
        key_aliases = {
            "queries": ("查询", "查询词", "query", "search_queries"),
            "target_platforms": ("目标平台", "platforms", "target_platform"),
            "include_keywords": ("包含关键词", "include_keyword", "keywords"),
            "exclude_keywords": ("排除关键词", "exclude_keyword"),
            "rationale": ("理由", "rationale_text", "reason", "思路"),
        }
        for en_key, aliases in key_aliases.items():
            if en_key not in obj:
                for alias in aliases:
                    if alias in obj:
                        obj[en_key] = obj.pop(alias)
                        break

        # 确保 queries 是 list
        if isinstance(obj.get("queries"), list):
            return obj
        return {}

    # ==================== 阶段2：搜索 ====================

    def collect_search_results(
        self,
        queries: List[str],
        max_results: int,
    ) -> List[Dict[str, Any]]:
        """阶段2 公开入口：执行多组搜索并汇总去重（按 link）。"""
        return self._collect_search_results(queries, max_results)

    def _collect_search_results(
        self,
        queries: List[str],
        max_results: int,
    ) -> List[Dict[str, Any]]:
        """执行多组搜索并汇总去重（按 link）"""
        return self._collect_search_results_detail(queries, max_results)["results"]

    def collect_search_results_detail(
        self,
        queries: List[str],
        max_results: int,
    ) -> Dict[str, Any]:
        """阶段2 公开入口（明细版）：返回汇总结果 + 每查询词命中明细，供执行可视化。"""
        return self._collect_search_results_detail(queries, max_results)

    def _collect_search_results_detail(
        self,
        queries: List[str],
        max_results: int,
    ) -> Dict[str, Any]:
        """执行多组搜索并汇总去重（按 link），同时记录每查询词的命中明细。"""
        all_results: List[Dict[str, Any]] = []
        seen_links: set = set()
        per_query: List[Dict[str, Any]] = []

        for query in queries:
            q_detail: Dict[str, Any] = {
                "query": query,
                "raw_count": 0,
                "new_count": 0,
                "error": None,
                "samples": [],
            }
            try:
                results = serpapi_search(query, num_results=max_results)
                q_detail["raw_count"] = len(results)
                for item in results:
                    link = item.get("link", "")
                    if link and link not in seen_links:
                        seen_links.add(link)
                        all_results.append(item)
                        q_detail["new_count"] += 1
                q_detail["samples"] = [
                    {
                        "title": it.get("title", ""),
                        "link": it.get("link", ""),
                        "snippet": (it.get("snippet", "") or "")[:200],
                    }
                    for it in results
                ]
            except Exception as e:
                print(f"[SearchAgent] 搜索 '{query}' 失败: {e}")
                q_detail["error"] = f"{type(e).__name__}: {e}"
                per_query.append(q_detail)
                continue
            per_query.append(q_detail)

        return {
            "results": all_results,
            "queries_detail": per_query,
        }

    # ==================== 阶段3：梳理（分批） ====================

    # 单批最大结果数。超过则分批喂给 LLM，避免一次性输出过长被 max_tokens 截断。
    # 经验值：每批 8 条，单批输出 JSON 约 1-2k token，远低于 8192 上限。
    EXTRACT_BATCH_SIZE = 8

    def extract_jobs(
        self,
        company_name: str,
        position_title: str,
        search_results: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        阶段3：用 LLM 从搜索结果中提取岗位开放信息（同步，source_url 必填）。

        搜索结果超过 EXTRACT_BATCH_SIZE 时自动分批，逐批提取后合并去重
        （按 source_url）。分批既避免单次输出 max_tokens 截断，也降低中转站
        偶发空 400 的概率（单次请求越小越稳）。

        Returns:
            招聘信息列表，每条 source_url 非空。失败返回 []。
        """
        if not search_results:
            return []

        batches = self._chunk(search_results, self.EXTRACT_BATCH_SIZE)
        print(f"[SearchAgent] 阶段3 分 {len(batches)} 批，每批≤{self.EXTRACT_BATCH_SIZE} 条")

        all_jobs: List[Dict[str, Any]] = []
        any_truncated = False
        self.last_extract_batches: List[Dict[str, Any]] = []
        for i, batch in enumerate(batches):
            print(f"[SearchAgent] 阶段3 第 {i + 1}/{len(batches)} 批（{len(batch)} 条）")
            # 构造本批 user_message 供可视化存储
            results_text = json.dumps(batch, ensure_ascii=False, indent=2)
            batch_user_message = f"""目标公司：{company_name}
目标职位：{position_title}

以下是搜索引擎返回的结果，请从中提取招聘信息（source_url 必填）：

{results_text}"""

            jobs = self._extract_one_batch(company_name, position_title, batch)
            truncated = self._last_output_truncated()
            if truncated:
                any_truncated = True
            all_jobs.extend(jobs)
            # 记录本批明细（输入摘要 + 原始输出 + 解析结果数 + finish），供可视化
            self.last_extract_batches.append({
                "index": i + 1,
                "input_count": len(batch),
                "output_count": len(jobs),
                "finish_reason": self._last_finish_reason,
                "truncated": truncated,
                "raw_output": (self.last_raw_output or "")[:4000],  # 限长防爆
                "user_message": batch_user_message,
            })

        # 按 source_url 去重（多批可能命中同一链接）
        seen: set = set()
        deduped: List[Dict[str, Any]] = []
        for j in all_jobs:
            url = (j.get("source_url") or "").strip()
            if not url or url in seen:
                continue
            seen.add(url)
            deduped.append(j)

        if any_truncated:
            print("[SearchAgent] 阶段3 至少一批输出被截断，结果可能不全")
        print(f"[SearchAgent] 阶段3 提取招聘信息: {len(deduped)} 条（去重前 {len(all_jobs)}）")
        return deduped

    def _chunk(self, items: List[Dict[str, Any]], size: int) -> List[List[Dict[str, Any]]]:
        """把列表切成固定大小的批。"""
        return [items[i:i + size] for i in range(0, len(items), size)]

    def _extract_one_batch(
        self,
        company_name: str,
        position_title: str,
        batch: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """对一批搜索结果执行一次 LLM 提取，返回解析出的岗位列表（source_url 已兜底非空）。"""
        results_text = json.dumps(batch, ensure_ascii=False, indent=2)

        user_message = f"""目标公司：{company_name}
目标职位：{position_title}

以下是搜索引擎返回的结果，请从中提取招聘信息（source_url 必填）：

{results_text}"""

        self.last_extract_system_prompt = EXTRACT_SYSTEM_PROMPT

        try:
            output = self._call_llm_with_retry(
                messages=[
                    {"role": "system", "content": EXTRACT_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                # 推理模型（如 mimo-v2.5-pro）先输出约 3-5k token 的
                # reasoning_content，之后才出 content。3072 会被 reasoning 吃光、
                # content 根本不产出。8192 实测能让 content 带着完整 JSON 正常返回。
                max_tokens=8192,
            )
            self.last_raw_output = output
            print(f"[SearchAgent] 阶段3 本批 LLM输出长度: {len(output)} (finish={self._last_finish_reason})")

            jobs = self._parse_jobs_output(output)
            jobs = [j for j in jobs if (j.get("source_url") or "").strip()]
            return jobs

        except Exception as e:
            print(f"[SearchAgent] 阶段3 提取失败: {e}")
            import traceback
            traceback.print_exc()
            self.last_raw_output = f"[LLM_CALL_ERROR] {type(e).__name__}: {e}"
            return []

    def _parse_jobs_output(self, output: str) -> List[Dict[str, Any]]:
        """解析阶段3 的 JSON 数组输出"""
        if not output:
            return []
        output = output.strip()
        if output.startswith("```"):
            output = re.sub(r"^```(?:json)?\s*", "", output)
            output = re.sub(r"\s*```$", "", output)
            output = output.strip()

        try:
            if output.startswith("["):
                return json.loads(output)
            match = re.search(r"\[[\s\S]*\]", output)
            if match:
                return json.loads(match.group())
            if output.startswith("{"):
                obj = json.loads(output)
                return [obj]
            return []
        except json.JSONDecodeError as e:
            print(f"[SearchAgent] 阶段3 JSON解析失败: {e}")
            print(f"[SearchAgent] 原始输出: {output[:500]}")
            return []

    # ==================== 兼容旧内部方法（test-search 可能调用） ====================

    def _build_queries(
        self,
        company_name: str,
        position: str,
        locations: Optional[List[str]],
    ) -> List[str]:
        """保留旧方法以兼容 test-search 诊断接口（返回兜底模板）"""
        return [
            f"{company_name} {position} 招聘",
            f"{company_name} 社招 {position}",
            f"{company_name} {position} boss直聘",
        ]


# 全局Agent实例
_search_agent: Optional[SearchAgent] = None


def get_search_agent() -> SearchAgent:
    """获取搜索Agent单例"""
    global _search_agent
    if _search_agent is None:
        _search_agent = SearchAgent()
    return _search_agent
