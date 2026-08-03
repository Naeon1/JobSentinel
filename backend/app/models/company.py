"""
公司模型
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text
from datetime import datetime
import uuid
import json

from app.core.config import CST
from app.models.database import Base

_now_cst = lambda: datetime.now(CST)


class Company(Base):
    """公司模型"""

    __tablename__ = "companies"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, comment="公司名称")
    aliases = Column(Text, comment="公司别名列表（JSON格式）")
    website = Column(String(255), comment="公司官网")
    career_page = Column(String(255), comment="招聘页面")
    industry = Column(String(50), comment="所属行业")
    notes = Column(Text, comment="备注")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=_now_cst, comment="创建时间")
    updated_at = Column(
        DateTime,
        default=_now_cst,
        onupdate=_now_cst,
        comment="更新时间"
    )

    def __repr__(self):
        return f"<Company(id={self.id}, name='{self.name}')>"

    def to_dict(self):
        """转换为字典"""
        aliases = []
        if self.aliases:
            try:
                aliases = json.loads(self.aliases)
            except (json.JSONDecodeError, TypeError):
                aliases = []

        return {
            "id": self.id,
            "name": self.name,
            "aliases": aliases,
            "website": self.website,
            "career_page": self.career_page,
            "industry": self.industry,
            "notes": self.notes,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
