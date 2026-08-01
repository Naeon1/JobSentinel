"""
公司相关的Pydantic Schema
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class CompanyBase(BaseModel):
    """公司基础Schema"""
    name: str = Field(..., min_length=1, max_length=100, description="公司名称")
    aliases: Optional[List[str]] = Field(default=[], description="公司别名")
    website: Optional[str] = Field(default=None, max_length=255, description="公司官网")
    career_page: Optional[str] = Field(default=None, max_length=255, description="招聘页面")
    industry: Optional[str] = Field(default=None, max_length=50, description="所属行业")
    notes: Optional[str] = Field(default=None, description="备注")


class CompanyCreate(CompanyBase):
    """创建公司请求Schema"""
    pass


class CompanyUpdate(BaseModel):
    """更新公司请求Schema"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100, description="公司名称")
    aliases: Optional[List[str]] = Field(default=None, description="公司别名")
    website: Optional[str] = Field(default=None, max_length=255, description="公司官网")
    career_page: Optional[str] = Field(default=None, max_length=255, description="招聘页面")
    industry: Optional[str] = Field(default=None, max_length=50, description="所属行业")
    notes: Optional[str] = Field(default=None, description="备注")
    is_active: Optional[bool] = Field(default=None, description="是否启用")


class CompanyResponse(CompanyBase):
    """公司响应Schema"""
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

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
            if field == 'aliases' and isinstance(value, str):
                try:
                    value = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    value = []
            data[field] = value
        return cls(**data)


class CompanyListResponse(BaseModel):
    """公司列表响应Schema"""
    items: List[CompanyResponse]
    total: int
    skip: int
    limit: int
