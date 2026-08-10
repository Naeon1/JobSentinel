"""邮件通知记录API

提供邮件发送记录的查询与删除，供前端「邮件通知」页面使用。
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.email_log import EmailLog

router = APIRouter(prefix="/api/email-logs", tags=["邮件通知记录"])


@router.get("/")
async def list_email_logs(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    status: Optional[str] = Query(None, description="发送状态: success/failed/skipped"),
    trigger_type: Optional[str] = Query(None, description="触发来源: manual/scheduled"),
    db: Session = Depends(get_db),
):
    """获取邮件通知记录列表（按创建时间倒序）"""
    query = db.query(EmailLog)

    if status:
        query = query.filter(EmailLog.status == status)
    if trigger_type:
        query = query.filter(EmailLog.trigger_type == trigger_type)

    total = query.count()
    results = query.order_by(EmailLog.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "items": [r.to_dict() for r in results],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.delete("/{log_id}")
async def delete_email_log(
    log_id: str,
    db: Session = Depends(get_db),
):
    """删除单条邮件通知记录"""
    log = db.query(EmailLog).filter(EmailLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="邮件通知记录不存在")

    db.delete(log)
    db.commit()
    return {"message": "邮件通知记录已删除"}
