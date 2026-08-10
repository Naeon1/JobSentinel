"""
邮件服务API

提供邮件配置测试和状态查询功能。
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.models.database import get_db
from app.core.config import settings
from app.services.email_service import EmailService


router = APIRouter(prefix="/api/email", tags=["邮件服务"])


class TestEmailRequest(BaseModel):
    """测试邮件请求"""
    recipients: Optional[List[str]] = None


class EmailConfigResponse(BaseModel):
    """邮件配置响应"""
    configured: bool
    smtp_host: str
    smtp_port: int
    smtp_username: Optional[str]
    email_from: Optional[str]
    recipient_count: int


@router.get("/config", response_model=EmailConfigResponse)
async def get_email_config():
    """获取邮件配置状态。

    Returns:
        邮件配置信息（密码不返回）
    """
    return EmailConfigResponse(
        configured=bool(settings.SMTP_USERNAME and settings.SMTP_PASSWORD),
        smtp_host=settings.SMTP_HOST,
        smtp_port=settings.SMTP_PORT,
        smtp_username=settings.SMTP_USERNAME,
        email_from=settings.EMAIL_FROM,
        recipient_count=len(settings.EMAIL_TO_LIST),
    )


@router.post("/test")
async def test_email(request: TestEmailRequest, db: Session = Depends(get_db)):
    """发送测试邮件。

    Args:
        request: 测试邮件请求（可指定收件人）

    Returns:
        发送结果
    """
    # 使用指定的收件人或默认配置的收件人
    recipients = request.recipients or settings.EMAIL_TO_LIST

    if not recipients:
        raise HTTPException(
            status_code=400,
            detail="未配置收件人，请在请求中指定 recipients 或在 .env 中配置 EMAIL_TO_LIST"
        )

    email_service = EmailService(db)
    success, message = email_service.send_test_email(recipients)

    if not success:
        raise HTTPException(status_code=500, detail=message)

    return {
        "success": True,
        "message": message,
        "recipients": recipients,
    }
