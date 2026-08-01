"""
职位配置相关的Pydantic Schema
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID


class PositionBase(BaseModel):
    """职位配置基础Schema"""
    title: str = Field(..., min_length=1, max_length=100, description="职位名称")
    keywords: Optional[List[str]] = Field(default=[], description="搜索关键词")
    exclude_keywords: Optional[List[str]] = Field(default=[], description="排除关键词")
    locations: Optional[List[str]] = Field(default=[], description="目标城市")
    experience_level: Optional[str] = Field(
        default=None,
        description="经验要求: junior/mid/senior"
    )


class PositionCreate(PositionBase):
    """创建职位配置请求Schema"""
    pass


class PositionUpdate(BaseModel):
    """更新职位配置请求Schema"""
    title: Optional[str] = Field(default=None, min_length=1, max_length=100, description="职位名称")
    keywords: Optional[List[str]] = Field(default=None, description="搜索关键词")
    exclude_keywords: Optional[List[str]] = Field(default=None, description="排除关键词")
    locations: Optional[List[str]] = Field(default=None, description="目标城市")
    experience_level: Optional[str] = Field(default=None, description="经验要求")
    is_active: Optional[bool] = Field(default=None, description="是否启用")


class PositionResponse(PositionBase):
    """职位配置响应Schema"""
    id: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        """从ORM对象创建，处理JSON字段"""
        import json
        data = {}
        for field in cls.model_fields:
            value = getattr(obj, field, None)
            # 将JSON字符串转换为list
            if field in ('keywords', 'exclude_keywords', 'locations') and isinstance(value, str):
                try:
                    value = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    value = []
            data[field] = value
        return cls(**data)


class PositionListResponse(BaseModel):
    """职位配置列表响应Schema"""
    items: List[PositionResponse]
    total: int
    skip: int
    limit: int
