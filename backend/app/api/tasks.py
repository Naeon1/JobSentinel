"""
任务执行API
"""

import asyncio
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.models.database import get_db, SessionLocal
from app.models.company import Company
from app.models.position import PositionConfig
from app.models.job import SearchTask
from app.schemas.job import RunSearchRequest
from app.services.search_service import SearchService
from app.services.email_service import EmailService, record_email_log

router = APIRouter(prefix="/api/tasks", tags=["任务执行"])


def run_search_background(task_ids: list):
    """后台执行预创建的搜索任务（同步函数，FastAPI 会自动在线程池中运行）。

    每个任务内部已有 try/except 把自己标 failed，外加这里的兜底，
    确保不会出现"僵尸 running"任务。
    搜索完成后自动发送邮件报告（如果配置了邮件服务）。
    """
    db = SessionLocal()
    results = []
    try:
        search_service = SearchService(db)
        results = search_service.run_existing_tasks(task_ids)
    except Exception as e:
        import traceback
        traceback.print_exc()
        # 最后兜底：把仍在 running/planning 的任务标 failed
        try:
            for tid in task_ids:
                t = db.query(SearchTask).filter(SearchTask.id == tid).first()
                if t and t.status not in ("completed", "failed"):
                    search_service._mark_task_failed(t, f"后台执行异常: {e}")
        except Exception as e2:
            print(f"[run_search_background] 兜底标记失败: {e2}")
    finally:
        db.close()

    # 发送邮件报告（无论成功/失败/跳过都落库一条 EmailLog）
    if results:
        log_db = SessionLocal()
        try:
            email_service = EmailService()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            outcome = loop.run_until_complete(email_service.send_search_report(results))
            loop.close()
            record_email_log(log_db, trigger_type="manual", task_results=results, send_outcome=outcome)
        except Exception as e:
            print(f"[run_search_background] 发送邮件报告失败: {e}")
            try:
                record_email_log(
                    log_db,
                    trigger_type="manual",
                    task_results=results,
                    send_outcome={
                        "success": False,
                        "skipped": False,
                        "subject": None,
                        "recipients": [],
                        "error": str(e),
                        "duration_ms": 0,
                    },
                )
            except Exception:
                pass
        finally:
            log_db.close()


@router.post("/run")
async def run_search(
    request: RunSearchRequest = None,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
):
    """手动触发搜索任务。

    先在主请求里预创建本批次的 SearchTask 记录（status=planning），
    立即返回 task_id 列表供前端轮询；后台线程再异步执行三阶段流水线。
    """
    if request is None:
        request = RunSearchRequest()

    print(f"[DEBUG] RunSearchRequest: company_id={request.company_id}, position_id={request.position_id}")

    # 验证公司是否存在
    if request.company_id:
        company = db.query(Company).filter(Company.id == request.company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="公司不存在")

    # 验证职位配置是否存在
    if request.position_id:
        position = db.query(PositionConfig).filter(
            PositionConfig.id == request.position_id
        ).first()
        if not position:
            raise HTTPException(status_code=404, detail="职位配置不存在")

    # 预创建任务记录（拿到 task_ids）
    search_service = SearchService(db)
    tasks = search_service.prepare_batch_tasks(
        company_id=str(request.company_id) if request.company_id else None,
        position_id=str(request.position_id) if request.position_id else None,
    )
    task_ids = [str(t.id) for t in tasks]

    if not task_ids:
        raise HTTPException(status_code=400, detail="没有可执行的公司×职位组合（请先配置并启用公司和职位）")

    # 后台异步执行
    background_tasks.add_task(run_search_background, task_ids)

    return {
        "message": f"已启动 {len(task_ids)} 个搜索任务",
        "task_ids": task_ids,
        "company_id": str(request.company_id) if request.company_id else None,
        "position_id": str(request.position_id) if request.position_id else None,
    }
