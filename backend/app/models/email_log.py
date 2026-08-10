"""
邮件通知记录模型

记录每次搜索报告邮件的发送结果（批次级，一封邮件覆盖该批次所有 task）。
与 SearchTask 的 steps_log（per-task）解耦，独立存放，便于在「邮件通知」
页面查询每次发送的成败、收件人、主题、触发来源与错误信息。
"""

from sqlalchemy import Column, String, Text, Integer, DateTime
from datetime import datetime
import uuid
import json

from app.core.config import CST
from app.models.database import Base

_now_cst = lambda: datetime.now(CST)


class EmailLog(Base):
    """邮件通知记录模型"""

    __tablename__ = "email_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    trigger_type = Column(String(20), comment="触发来源: manual/scheduled")
    status = Column(String(20), comment="发送状态: success/failed/skipped")
    subject = Column(String(255), comment="邮件主题")
    recipients = Column(Text, comment="收件人地址列表（JSON格式）")
    task_count = Column(Integer, default=0, comment="本批次任务总数")
    job_count = Column(Integer, default=0, comment="本批次合计 jobs_found")
    task_ids = Column(Text, comment="关联的任务ID列表（JSON格式）")
    error_message = Column(Text, comment="失败/跳过原因（成功为 None）")
    duration_ms = Column(Integer, default=0, comment="发送耗时（毫秒）")
    created_at = Column(DateTime, default=_now_cst, comment="记录创建时间")

    def __repr__(self):
        return f"<EmailLog(id={self.id}, status='{self.status}', trigger='{self.trigger_type}')>"

    def to_dict(self):
        """转换为字典"""
        recipients = []
        if self.recipients:
            try:
                recipients = json.loads(self.recipients)
            except (json.JSONDecodeError, TypeError):
                recipients = []

        task_ids = []
        if self.task_ids:
            try:
                task_ids = json.loads(self.task_ids)
            except (json.JSONDecodeError, TypeError):
                task_ids = []

        return {
            "id": self.id,
            "trigger_type": self.trigger_type,
            "status": self.status,
            "subject": self.subject,
            "recipients": recipients,
            "task_count": self.task_count or 0,
            "job_count": self.job_count or 0,
            "task_ids": task_ids,
            "error_message": self.error_message,
            "duration_ms": self.duration_ms or 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
