"""
定时任务配置模型
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer
from datetime import datetime
import uuid

from app.models.database import Base


class Schedule(Base):
    """定时任务配置模型"""

    __tablename__ = "schedules"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), comment="任务名称")
    cron_expression = Column(String(50), comment="Cron表达式")
    is_active = Column(Boolean, default=True, comment="是否启用")
    last_run_at = Column(DateTime, comment="上次执行时间")
    next_run_at = Column(DateTime, comment="下次执行时间")
    config = Column(Text, comment="任务配置（JSON格式）")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    def __repr__(self):
        return f"<Schedule(id={self.id}, name='{self.name}')>"

    def to_dict(self):
        """转换为字典"""
        import json
        config = None
        if self.config:
            try:
                config = json.loads(self.config)
            except (json.JSONDecodeError, TypeError):
                config = self.config

        return {
            "id": self.id,
            "name": self.name,
            "cron_expression": self.cron_expression,
            "is_active": self.is_active,
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "next_run_at": self.next_run_at.isoformat() if self.next_run_at else None,
            "config": config,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class EmailConfig(Base):
    """邮件配置模型"""

    __tablename__ = "email_configs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    smtp_host = Column(String(100), comment="SMTP服务器")
    smtp_port = Column(Integer, comment="SMTP端口")
    username = Column(String(100), comment="用户名")
    password_encrypted = Column(String(255), comment="加密后的密码")
    from_address = Column(String(100), comment="发件人地址")
    to_addresses = Column(Text, comment="收件人地址列表（JSON格式）")
    is_active = Column(Boolean, default=True, comment="是否启用")

    def __repr__(self):
        return f"<EmailConfig(id={self.id}, smtp_host='{self.smtp_host}')>"

    def to_dict(self):
        """转换为字典"""
        import json
        to_addresses = []
        if self.to_addresses:
            try:
                to_addresses = json.loads(self.to_addresses)
            except (json.JSONDecodeError, TypeError):
                to_addresses = []

        return {
            "id": self.id,
            "smtp_host": self.smtp_host,
            "smtp_port": self.smtp_port,
            "username": self.username,
            "from_address": self.from_address,
            "to_addresses": to_addresses,
            "is_active": self.is_active,
        }
