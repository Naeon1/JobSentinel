"""
职位配置模型
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text
from datetime import datetime
import uuid
import json

from app.core.config import CST
from app.models.database import Base

_now_cst = lambda: datetime.now(CST)


class PositionConfig(Base):
    """职位配置模型"""

    __tablename__ = "position_configs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(100), nullable=False, comment="职位名称")
    keywords = Column(Text, comment="搜索关键词（JSON格式）")
    exclude_keywords = Column(Text, comment="排除关键词（JSON格式）")
    locations = Column(Text, comment="目标城市（JSON格式）")
    experience_level = Column(
        String(20),
        comment="经验要求: junior/mid/senior"
    )
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=_now_cst, comment="创建时间")

    def __repr__(self):
        return f"<PositionConfig(id={self.id}, title='{self.title}')>"

    def to_dict(self):
        """转换为字典"""
        keywords = []
        exclude_keywords = []
        locations = []

        if self.keywords:
            try:
                keywords = json.loads(self.keywords)
            except (json.JSONDecodeError, TypeError):
                keywords = []

        if self.exclude_keywords:
            try:
                exclude_keywords = json.loads(self.exclude_keywords)
            except (json.JSONDecodeError, TypeError):
                exclude_keywords = []

        if self.locations:
            try:
                locations = json.loads(self.locations)
            except (json.JSONDecodeError, TypeError):
                locations = []

        return {
            "id": self.id,
            "title": self.title,
            "keywords": keywords,
            "exclude_keywords": exclude_keywords,
            "locations": locations,
            "experience_level": self.experience_level,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
