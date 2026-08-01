"""
搜索服务模块
管理搜索任务的执行和结果存储
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.position import PositionConfig
from app.models.job import SearchTask, JobListing
from app.agents.search_agent import get_search_agent


class SearchService:
    """搜索服务"""

    def __init__(self, db: Session):
        self.db = db
        self.agent = get_search_agent()

    def run_search_task(
        self,
        company_id: str,
        position_id: str,
    ) -> Dict[str, Any]:
        """创建并执行单次搜索任务（兼容旧调用方）。"""
        task = self._create_task(company_id, position_id)
        return self._execute_task(task)

    def _create_task(
        self,
        company_id: str,
        position_id: str,
    ) -> SearchTask:
        """创建一条搜索任务记录（status=planning, progress=0），返回该 task。"""
        # 取职位名冗余写入
        position = self.db.query(PositionConfig).filter(
            PositionConfig.id == position_id
        ).first()
        task = SearchTask(
            company_id=company_id,
            position_config_id=position_id,
            status="planning",
            current_step="planning",
            progress=0,
            steps_log=json.dumps([], ensure_ascii=False),
            position_title=position.title if position else None,
            started_at=datetime.utcnow(),
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def _execute_task(self, task: SearchTask) -> Dict[str, Any]:
        """
        执行一个已创建的搜索任务（同步，分阶段写进度）。

        三阶段：plan_search → 搜索 → extract_jobs。每阶段前后更新 task 的
        current_step / progress / steps_log 并 commit，供前端轮询可视化。

        Args:
            task: 已创建的 SearchTask 记录

        Returns:
            任务执行结果
        """
        try:
            # 获取公司和职位配置
            company = self.db.query(Company).filter(Company.id == task.company_id).first()
            position = self.db.query(PositionConfig).filter(
                PositionConfig.id == task.position_config_id
            ).first()

            if not company or not position:
                raise ValueError("公司或职位配置不存在")

            # 冗余职位名（_create_task 可能没取到）
            if not task.position_title:
                task.position_title = position.title

            company_dict = company.to_dict()
            position_dict = position.to_dict()

            # ---- 阶段1：规划 ----
            self._update_progress(task, "planning", "start", "正在让 AI 规划搜索策略…", 5)
            plan = self.agent.plan_search(company_dict, position_dict)
            rationale = plan.get("rationale") if isinstance(plan, dict) else None
            qcount = len(plan.get("queries", [])) if isinstance(plan, dict) else 0
            self._update_progress(
                task, "planning", "done",
                f"AI 生成了 {qcount} 条搜索策略。{rationale or ''}".strip(),
                20,
                detail={
                    "phase": "planning",
                    "plan_queries": plan.get("queries", []) if isinstance(plan, dict) else [],
                    "target_platforms": plan.get("target_platforms", []) if isinstance(plan, dict) else [],
                    "include_keywords": plan.get("include_keywords", []) if isinstance(plan, dict) else [],
                    "exclude_keywords": plan.get("exclude_keywords", []) if isinstance(plan, dict) else [],
                    "rationale": rationale,
                    "llm_raw_output": (getattr(self.agent, "last_plan_output", "") or "")[:4000],
                    "system_prompt": (getattr(self.agent, "last_plan_system_prompt", "") or "")[:6000],
                    "user_message": (getattr(self.agent, "last_plan_user_message", "") or "")[:6000],
                },
            )

            queries = plan.get("queries", []) if isinstance(plan, dict) else []
            if not queries:
                task.status = "completed"
                task.current_step = "done"
                task.progress = 100
                task.jobs_found = 0
                task.completed_at = datetime.utcnow()
                self._append_step(task, "done", "done", "策略无查询词，任务结束", 100)
                self.db.commit()
                return {
                    "task_id": str(task.id),
                    "status": "completed",
                    "jobs_found": 0,
                    "company_name": company.name,
                    "position_title": position.title,
                }

            # ---- 阶段2：搜索 ----
            self._update_progress(task, "searching", "start", "正在执行搜索引擎查询…", 25)
            search_detail = self.agent.collect_search_results_detail(queries, 10)
            search_results = search_detail["results"]
            queries_detail = search_detail["queries_detail"]
            self._update_progress(
                task, "searching", "done",
                f"搜索到 {len(search_results)} 条网页结果，准备交给 AI 梳理",
                55,
                detail={
                    "phase": "searching",
                    "total_results": len(search_results),
                    "queries_count": len(queries),
                    "queries_detail": queries_detail,  # 每查询词命中/样例/错误
                },
            )

            # ---- 阶段3：梳理 ----
            jobs_data: List[Dict[str, Any]] = []
            if search_results:
                self._update_progress(task, "extracting", "start", "AI 正在梳理岗位开放情况…", 60)
                jobs_data = self.agent.extract_jobs(
                    company.name, position.title, search_results
                )
                extract_batches = getattr(self.agent, "last_extract_batches", []) or []
                self._update_progress(
                    task, "extracting", "done",
                    f"AI 识别出 {len(jobs_data)} 条在招岗位信息",
                    85,
                    detail={
                        "phase": "extracting",
                        "extracted_count": len(jobs_data),
                        "batch_count": len(extract_batches),
                        "system_prompt": (getattr(self.agent, "last_extract_system_prompt", "") or "")[:6000],
                        "user_message": (getattr(self.agent, "last_extract_user_message", "") or "")[:6000],
                        "batches": extract_batches,  # 各批输入/原始输出/finish
                    },
                )

            # 保存搜索结果（source_url 为空的会被丢弃）
            save_stat = self._save_jobs(jobs_data, company.id, task.id)
            saved_count = save_stat["saved"]

            # ---- 完成 ----
            task.status = "completed"
            task.current_step = "done"
            task.progress = 100
            task.completed_at = datetime.utcnow()
            task.jobs_found = saved_count
            self._append_step(
                task, "done", "done",
                f"任务完成，入库 {saved_count} 条岗位信息", 100,
                detail={
                    "phase": "done",
                    "input_count": len(jobs_data),
                    "saved_count": save_stat["saved"],
                    "duplicated_count": save_stat["duplicated"],
                    "skipped_no_url_count": save_stat["skipped_no_url"],
                    "failed_count": save_stat["failed"],
                },
            )
            self.db.commit()

            return {
                "task_id": str(task.id),
                "status": "completed",
                "jobs_found": saved_count,
                "company_name": company.name,
                "position_title": position.title,
            }

        except Exception as e:
            # 更新任务状态为失败（同步更新进度日志 + 当前步骤 error）
            import traceback
            tb = traceback.format_exc()
            task.status = "failed"
            task.error_message = str(e)
            task.completed_at = datetime.utcnow()
            self._append_step(task, task.current_step or "planning", "error", f"失败: {e}", task.progress or 0)
            self.db.commit()
            print(f"[SearchService] 任务 {task.id} 失败: {e}\n{tb}")

            return {
                "task_id": str(task.id),
                "status": "failed",
                "error": str(e),
            }

    # ==================== 进度写入 ====================

    def _update_progress(
        self,
        task: SearchTask,
        step: str,
        status: str,
        message: str,
        progress: int,
        detail: Optional[Dict[str, Any]] = None,
    ) -> None:
        """更新任务进度：设当前阶段+进度百分比，并追加一条步骤日志，立即 commit。

        detail：可选的执行中间数据（喂给 LLM 的 prompt、搜索明细、LLM 原始输出、
        去重统计等），会原样存进 steps_log 这一条的 detail 字段，供前端可视化展开。
        """
        task.current_step = step
        task.progress = progress
        self._append_step(task, step, status, message, progress, detail=detail)
        self.db.commit()

    def _append_step(
        self,
        task: SearchTask,
        step: str,
        status: str,
        message: str,
        progress: int,
        detail: Optional[Dict[str, Any]] = None,
    ) -> None:
        """向 task.steps_log 追加一条记录（不单独 commit，由调用方负责）。"""
        logs: List[Dict[str, Any]] = []
        if task.steps_log:
            try:
                logs = json.loads(task.steps_log)
            except (json.JSONDecodeError, TypeError):
                logs = []
        entry: Dict[str, Any] = {
            "step": step,
            "status": status,
            "message": message,
            "progress": progress,
            "timestamp": datetime.utcnow().isoformat(),
        }
        if detail is not None:
            entry["detail"] = detail
        logs.append(entry)
        task.steps_log = json.dumps(logs, ensure_ascii=False)

    def _collect_pairs(
        self,
        company_id: Optional[str] = None,
        position_id: Optional[str] = None,
    ) -> List[tuple]:
        """根据筛选条件收集要执行的 (company_id, position_id) 组合。"""
        pairs = []
        if company_id and position_id:
            pairs.append((company_id, position_id))
        elif company_id:
            positions = self.db.query(PositionConfig).filter(
                PositionConfig.is_active == True
            ).all()
            for pos in positions:
                pairs.append((company_id, pos.id))
        elif position_id:
            companies = self.db.query(Company).filter(
                Company.is_active == True
            ).all()
            for company in companies:
                pairs.append((company.id, position_id))
        else:
            companies = self.db.query(Company).filter(
                Company.is_active == True
            ).all()
            positions = self.db.query(PositionConfig).filter(
                PositionConfig.is_active == True
            ).all()
            for company in companies:
                for pos in positions:
                    pairs.append((company.id, pos.id))
        return pairs

    def _resolve_company_position(self, company_id: str, position_id: str):
        company = self.db.query(Company).filter(Company.id == company_id).first()
        position = self.db.query(PositionConfig).filter(
            PositionConfig.id == position_id
        ).first()
        return company, position

    def prepare_batch_tasks(
        self,
        company_id: Optional[str] = None,
        position_id: Optional[str] = None,
    ) -> List[SearchTask]:
        """
        预创建本次批次的所有 SearchTask 记录（status=planning）并立即 commit，
        返回 task 列表供前端立即拿到 task_ids 进行轮询。后台再异步执行。

        若组合对应的公司或职位不存在，该组合会被跳过。
        """
        pairs = self._collect_pairs(company_id, position_id)
        tasks: List[SearchTask] = []
        for cid, pid in pairs:
            company, position = self._resolve_company_position(cid, pid)
            if not company or not position:
                continue
            task = SearchTask(
                company_id=cid,
                position_config_id=pid,
                status="planning",
                current_step="planning",
                progress=0,
                steps_log=json.dumps([], ensure_ascii=False),
                position_title=position.title,
                started_at=datetime.utcnow(),
            )
            self.db.add(task)
            tasks.append(task)
        self.db.commit()
        for t in tasks:
            self.db.refresh(t)
        return tasks

    def run_existing_tasks(self, task_ids: List[str]) -> List[Dict[str, Any]]:
        """
        按给定 task_ids 依次执行已创建的任务（供后台线程调用）。
        每个任务用独立 try/except，单个失败不影响其他，并把自己标 failed。
        """
        results = []
        for tid in task_ids:
            task = self.db.query(SearchTask).filter(SearchTask.id == tid).first()
            if not task:
                results.append({"task_id": tid, "status": "failed", "error": "任务不存在"})
                continue
            try:
                result = self._execute_task(task)
                results.append(result)
            except Exception as e:
                # 兜底：保证不会留僵尸 running
                self._mark_task_failed(task, str(e))
                results.append({"task_id": tid, "status": "failed", "error": str(e)})
        return results

    def _mark_task_failed(self, task: SearchTask, message: str) -> None:
        """把任务标记为失败（防止僵尸 running）。"""
        try:
            task.status = "failed"
            task.error_message = message
            task.completed_at = datetime.utcnow()
            self._append_step(
                task, task.current_step or "planning", "error", f"失败: {message}", task.progress or 0
            )
            self.db.commit()
        except Exception as e:
            print(f"[SearchService] 标记任务失败时出错: {e}")

    def run_batch_search(
        self,
        company_id: Optional[str] = None,
        position_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        批量执行搜索任务（预创建 + 同步执行，兼容旧调用方）。

        Args:
            company_id: 指定公司ID（可选，不指定则搜索所有）
            position_id: 指定职位配置ID（可选，不指定则搜索所有）

        Returns:
            所有任务执行结果
        """
        tasks = self.prepare_batch_tasks(company_id, position_id)
        return self.run_existing_tasks([str(t.id) for t in tasks])

    def _save_jobs(
        self,
        jobs_data: List[Dict[str, Any]],
        company_id: str,
        task_id: str,
    ) -> Dict[str, int]:
        """
        保存招聘信息到数据库

        Args:
            jobs_data: 招聘信息列表
            company_id: 公司ID
            task_id: 任务ID

        Returns:
            统计 dict: {saved, duplicated, skipped_no_url, failed}
            - saved: 成功新建/更新的条数
            - duplicated: 因 source_url 已存在而命中"更新旧记录"的条数（也算 saved）
            - skipped_no_url: source_url 为空被丢弃的条数
            - failed: 循环内异常的条数
        """
        stat = {"saved": 0, "duplicated": 0, "skipped_no_url": 0, "failed": 0}

        for job_data in jobs_data:
            try:
                # 链接必填兜底：source_url 为空一律不入库
                source_url = (job_data.get("source_url") or "").strip()
                if not source_url:
                    stat["skipped_no_url"] += 1
                    continue

                # is_open 归一为字符串: true/false/unknown
                is_open_raw = job_data.get("is_open", "unknown")
                if isinstance(is_open_raw, bool):
                    is_open = "true" if is_open_raw else "false"
                else:
                    is_open = str(is_open_raw).lower() if is_open_raw else "unknown"
                    if is_open not in ("true", "false", "unknown"):
                        is_open = "unknown"

                # 转换薪资为整数
                salary_min = self._parse_salary(job_data.get("salary_min"))
                salary_max = self._parse_salary(job_data.get("salary_max"))

                # 解析发布时间
                published_at = self._parse_datetime(job_data.get("published_at"))

                # 生成source_id用于去重
                source_id = self._generate_source_id(job_data)

                # 检查是否已存在
                existing = self.db.query(JobListing).filter(
                    JobListing.source_platform == job_data.get("source_platform"),
                    JobListing.source_id == source_id,
                ).first()

                if existing:
                    # 更新已有记录
                    existing.job_title = job_data.get("job_title", existing.job_title)
                    existing.is_open = is_open
                    existing.salary_min = salary_min or existing.salary_min
                    existing.salary_max = salary_max or existing.salary_max
                    existing.salary_description = job_data.get("salary_description", existing.salary_description)
                    existing.location = job_data.get("location", existing.location)
                    existing.experience_years = job_data.get("experience_years", existing.experience_years)
                    existing.education = job_data.get("education", existing.education)
                    # skills/benefits 是 Text 列，存 JSON 字符串（兼容旧值与 None）
                    existing.skills = self._dump_json_list(job_data.get("skills", existing.skills))
                    existing.job_description = job_data.get("job_description", existing.job_description)
                    existing.requirements = job_data.get("requirements", existing.requirements)
                    existing.benefits = self._dump_json_list(job_data.get("benefits", existing.benefits))
                    existing.crawled_at = datetime.utcnow()
                    stat["duplicated"] += 1
                else:
                    # 创建新记录
                    job = JobListing(
                        task_id=task_id,
                        company_id=company_id,
                        job_title=job_data.get("job_title", "未知职位"),
                        is_open=is_open,
                        salary_min=salary_min,
                        salary_max=salary_max,
                        salary_description=job_data.get("salary_description"),
                        location=job_data.get("location"),
                        experience_years=job_data.get("experience_years"),
                        education=job_data.get("education"),
                        skills=self._dump_json_list(job_data.get("skills")),
                        job_description=job_data.get("job_description"),
                        requirements=job_data.get("requirements"),
                        benefits=self._dump_json_list(job_data.get("benefits")),
                        source_platform=job_data.get("source_platform"),
                        source_url=source_url,
                        source_id=source_id,
                        published_at=published_at,
                        is_duplicate=False,
                        is_verified=False,
                    )
                    self.db.add(job)

                stat["saved"] += 1

            except Exception as e:
                stat["failed"] += 1
                print(f"保存招聘信息失败: {e}")
                continue

        self.db.commit()
        return stat

    def _dump_json_list(self, value: Any) -> Optional[str]:
        """把 list 序列化为 JSON 字符串存入 Text 列。
        None → None（保持可空）；已是 str（旧数据）→ 原样保留；
        其它非 list → None。"""
        if value is None:
            return None
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            return json.dumps(value, ensure_ascii=False)
        return None

    def _parse_salary(self, salary_value) -> Optional[int]:
        """解析薪资为整数（元/月）"""
        if salary_value is None:
            return None

        if isinstance(salary_value, (int, float)):
            return int(salary_value)

        if isinstance(salary_value, str):
            # 移除空格和单位
            salary_value = salary_value.strip().lower()

            # 处理"面议"
            if "面议" in salary_value or "negotiable" in salary_value:
                return None

            # 尝试提取数字
            import re
            numbers = re.findall(r'\d+', salary_value)
            if numbers:
                return int(numbers[0])

        return None

    def _parse_datetime(self, datetime_str) -> Optional[datetime]:
        """解析日期时间字符串"""
        if not datetime_str:
            return None

        try:
            from dateutil import parser
            return parser.parse(datetime_str)
        except:
            return None

    def _generate_source_id(self, job_data: Dict[str, Any]) -> str:
        """生成source_id用于去重"""
        import hashlib

        # 使用URL或标题+公司名生成唯一ID
        source_url = job_data.get("source_url", "")
        job_title = job_data.get("job_title", "")
        company_name = job_data.get("company_name", "")

        if source_url:
            return hashlib.md5(source_url.encode()).hexdigest()

        # 使用标题+公司名生成
        key = f"{job_title}_{company_name}"
        return hashlib.md5(key.encode()).hexdigest()
