"""
招聘信息API
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timedelta

from app.models.database import get_db
from app.models.job import JobListing, SearchTask
from app.models.company import Company
from app.schemas.job import (
    JobListingResponse,
    JobListingListResponse,
    SearchTaskResponse,
    SearchTaskListResponse,
    DashboardStats,
)

router = APIRouter(prefix="/api", tags=["招聘信息"])


# ==================== 测试接口 ====================

@router.get("/tasks/test-llm")
async def test_llm_connection():
    """测试LLM连接"""
    try:
        from app.core.config import settings
        from openai import AsyncOpenAI

        # 获取配置信息
        llm_info = {
            "provider": settings.LLM_PROVIDER,
            "api_base_url": settings.LLM_API_BASE_URL,
            "model_name": settings.LLM_MODEL_NAME,
            "use_anthropic_format": settings.LLM_USE_ANTHROPIC_FORMAT,
            "api_key_set": bool(settings.get_llm_api_key()),
        }

        # 使用openai库测试
        client = AsyncOpenAI(
            api_key=settings.get_llm_api_key(),
            base_url=settings.LLM_API_BASE_URL,
        )

        response = await client.chat.completions.create(
            model=settings.LLM_MODEL_NAME,
            messages=[
                {"role": "user", "content": "你好，请回复'连接成功'"}
            ],
            max_tokens=50,
        )

        content = response.choices[0].message.content

        return {
            "status": "success",
            "llm_info": llm_info,
            "response": content,
        }
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc(),
        }


@router.get("/tasks/test-search")
async def test_search_pipeline(
    company: str = Query("ByteDance", description="公司名称"),
    position: str = Query("Python", description="职位名称"),
    location: Optional[str] = Query(None, description="城市，逗号分隔"),
):
    """
    同步诊断接口：直接在请求里跑完整三阶段流水线（规划→搜索→梳理）并返回每步结果。
    用于定位搜索/LLM 到底卡在哪一步。不写数据库。
    """
    import traceback

    steps = {}
    try:
        from app.agents.search_agent import get_search_agent

        locations = [x.strip() for x in location.split(",")] if location else None

        agent = get_search_agent()
        steps["agent_created"] = True

        # 构造公司/职位 dict（诊断用，字段尽量贴近真实模型）
        company_dict = {
            "name": company,
            "aliases": [],
            "website": None,
            "career_page": None,
            "industry": None,
        }
        position_dict = {
            "title": position,
            "keywords": [],
            "exclude_keywords": [],
            "locations": locations or [],
            "experience_level": None,
        }

        # 阶段1：规划
        plan = agent.plan_search(company_dict, position_dict)
        steps["plan_queries_count"] = len(plan.get("queries", [])) if plan else 0
        steps["plan"] = plan if plan else None

        # 阶段2：搜索
        queries = plan.get("queries", []) if plan else []
        search_results = agent.collect_search_results(queries, 5) if queries else []
        steps["search_results_count"] = len(search_results)

        # 阶段3：梳理
        jobs = agent.extract_jobs(company, position, search_results) if search_results else []
        steps["llm_extracted_count"] = len(jobs)

        return {
            "status": "success",
            "steps": steps,
            "search_sample": search_results[:3],
            "jobs": jobs,
            "llm_plan_output": agent.last_plan_output,
            "llm_extract_output": agent.last_raw_output,
        }
    except Exception as e:
        return {
            "status": "error",
            "steps": steps,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }


# ==================== 招聘信息接口 ====================

@router.get("/jobs/", response_model=JobListingListResponse)
async def list_jobs(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    company_id: Optional[str] = Query(None, description="公司ID"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    location: Optional[str] = Query(None, description="工作地点"),
    salary_min: Optional[int] = Query(None, description="最低薪资"),
    salary_max: Optional[int] = Query(None, description="最高薪资"),
    source_platform: Optional[str] = Query(None, description="来源平台"),
    is_verified: Optional[bool] = Query(None, description="是否已验证"),
    db: Session = Depends(get_db),
):
    """获取招聘信息列表"""
    query = db.query(JobListing).join(
        Company, JobListing.company_id == Company.id
    ).add_columns(Company.name.label("company_name"))

    # 筛选条件
    if company_id:
        query = query.filter(JobListing.company_id == company_id)
    if keyword:
        # skills 是 Text 列（JSON 字符串），不能用 ARRAY 的 .any()；
        # 用 ilike 在 job_title / job_description / skills 文本里模糊匹配。
        query = query.filter(
            or_(
                JobListing.job_title.ilike(f"%{keyword}%"),
                JobListing.job_description.ilike(f"%{keyword}%"),
                JobListing.skills.ilike(f"%{keyword}%"),
            )
        )
    if location:
        query = query.filter(JobListing.location.ilike(f"%{location}%"))
    if salary_min:
        query = query.filter(
            or_(
                JobListing.salary_max >= salary_min,
                JobListing.salary_min >= salary_min,
            )
        )
    if salary_max:
        query = query.filter(
            or_(
                JobListing.salary_min <= salary_max,
                JobListing.salary_max <= salary_max,
            )
        )
    if source_platform:
        query = query.filter(JobListing.source_platform == source_platform)
    if is_verified is not None:
        query = query.filter(JobListing.is_verified == is_verified)

    # 排除重复
    query = query.filter(JobListing.is_duplicate == False)

    # 获取总数
    total = query.count()

    # 分页查询
    results = query.order_by(JobListing.crawled_at.desc()).offset(skip).limit(limit).all()

    # 构建响应
    items = []
    for row in results:
        job = row[0]  # JobListing对象
        company_name = row[1]  # company_name
        job_dict = JobListingResponse.from_orm(job).dict()
        job_dict["company_name"] = company_name
        items.append(JobListingResponse(**job_dict))

    return JobListingListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/jobs/{job_id}", response_model=JobListingResponse)
async def get_job(
    job_id: str,
    db: Session = Depends(get_db),
):
    """获取单条招聘信息详情"""
    result = db.query(JobListing).join(
        Company, JobListing.company_id == Company.id
    ).add_columns(Company.name.label("company_name")).filter(
        JobListing.id == job_id
    ).first()

    if not result:
        raise HTTPException(status_code=404, detail="招聘信息不存在")

    job = result[0]
    company_name = result[1]
    job_dict = JobListingResponse.from_orm(job).dict()
    job_dict["company_name"] = company_name

    return JobListingResponse(**job_dict)


@router.delete("/jobs/{job_id}")
async def delete_job(
    job_id: str,
    db: Session = Depends(get_db),
):
    """删除招聘信息"""
    job = db.query(JobListing).filter(JobListing.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="招聘信息不存在")

    db.delete(job)
    db.commit()

    return {"message": "招聘信息已删除"}


# ==================== 搜索任务接口 ====================

@router.get("/tasks/", response_model=SearchTaskListResponse)
async def list_tasks(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    status: Optional[str] = Query(None, description="任务状态"),
    company_id: Optional[str] = Query(None, description="公司ID"),
    db: Session = Depends(get_db),
):
    """获取搜索任务列表"""
    query = db.query(SearchTask).join(
        Company, SearchTask.company_id == Company.id
    ).add_columns(Company.name.label("company_name"))

    # 筛选条件
    if status:
        query = query.filter(SearchTask.status == status)
    if company_id:
        query = query.filter(SearchTask.company_id == company_id)

    # 获取总数
    total = query.count()

    # 分页查询
    results = query.order_by(SearchTask.created_at.desc()).offset(skip).limit(limit).all()

    # 构建响应
    items = []
    for row in results:
        task = row[0]
        company_name = row[1]
        task_dict = SearchTaskResponse.from_orm(task).dict()
        task_dict["company_name"] = company_name
        items.append(SearchTaskResponse(**task_dict))

    return SearchTaskListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/tasks/{task_id}", response_model=SearchTaskResponse)
async def get_task(
    task_id: str,
    db: Session = Depends(get_db),
):
    """获取单个任务详情"""
    result = db.query(SearchTask).join(
        Company, SearchTask.company_id == Company.id
    ).add_columns(Company.name.label("company_name")).filter(
        SearchTask.id == task_id
    ).first()

    if not result:
        raise HTTPException(status_code=404, detail="任务不存在")

    task = result[0]
    company_name = result[1]
    task_dict = SearchTaskResponse.from_orm(task).dict()
    task_dict["company_name"] = company_name

    return SearchTaskResponse(**task_dict)


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: str,
    db: Session = Depends(get_db),
):
    """删除搜索任务"""
    task = db.query(SearchTask).filter(SearchTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    db.delete(task)
    db.commit()

    return {"message": "任务已删除"}


# ==================== 仪表盘接口 ====================

@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: Session = Depends(get_db),
):
    """获取仪表盘统计数据"""
    # 公司数量
    company_count = db.query(Company).filter(Company.is_active == True).count()

    # 招聘信息数量（排除重复）
    job_count = db.query(JobListing).filter(JobListing.is_duplicate == False).count()

    # 今日新增
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_count = db.query(JobListing).filter(
        JobListing.crawled_at >= today,
        JobListing.is_duplicate == False,
    ).count()

    # 任务数量
    task_count = db.query(SearchTask).count()

    return DashboardStats(
        company_count=company_count,
        job_count=job_count,
        today_count=today_count,
        task_count=task_count,
    )
