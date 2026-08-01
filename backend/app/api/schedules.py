"""
定时任务配置API
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.models.database import get_db
from app.models.schedule import Schedule
from app.core.config import settings
from app.scheduler import reschedule, get_next_run_time

router = APIRouter(prefix="/api/schedules", tags=["定时任务"])


class ScheduleUpdateRequest(BaseModel):
    """更新定时任务请求"""
    cron_expression: Optional[str] = None
    is_enabled: Optional[bool] = None


@router.get("/")
async def list_schedules(
    db: Session = Depends(get_db),
):
    """获取定时任务配置列表"""
    schedules = db.query(Schedule).all()
    return [s.to_dict() for s in schedules]


@router.get("/current")
async def get_current_schedule():
    """获取当前定时任务配置"""
    return {
        "cron_expression": settings.SCHEDULE_CRON,
        "is_enabled": settings.SCHEDULE_ENABLED,
        "next_run_at": get_next_run_time(),  # ISO 字符串或 None
    }


@router.put("/current")
async def update_current_schedule(
    request: ScheduleUpdateRequest,
):
    """更新当前定时任务配置"""
    # 注意：这只是临时修改，重启后会恢复
    # 持久化需要修改 .env 文件或数据库

    # 先校验 cron 表达式合法，避免保存了配置但调度器静默不生效
    if request.cron_expression is not None:
        try:
            from apscheduler.triggers.cron import CronTrigger
            CronTrigger.from_crontab(request.cron_expression)
        except Exception:
            raise HTTPException(
                status_code=400,
                detail=f"无效的 Cron 表达式：{request.cron_expression!r}",
            )

    if request.cron_expression is not None:
        settings.SCHEDULE_CRON = request.cron_expression
    if request.is_enabled is not None:
        settings.SCHEDULE_ENABLED = request.is_enabled

    # 热更新调度器（立即重排定时 job，无需重启进程）
    try:
        reschedule()
    except Exception as e:
        # 调度器热更新失败不应阻塞配置保存，仅告警
        print(f"[schedules] 调度器热更新失败：{e}")

    return {
        "cron_expression": settings.SCHEDULE_CRON,
        "is_enabled": settings.SCHEDULE_ENABLED,
        "next_run_at": get_next_run_time(),
        "message": "配置已更新（注意：重启后会恢复默认值）",
    }
