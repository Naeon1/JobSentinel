"""
招聘信息相关的Pydantic Schema
"""

from typing import List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID


class JobListingResponse(BaseModel):
    """招聘信息响应Schema"""
    id: UUID
    task_id: Optional[UUID]
    company_id: UUID
    company_name: Optional[str] = None  # 关联查询获取

    job_title: str
    is_open: Optional[str] = None  # true/false/unknown：是否在招
    salary_min: Optional[int]
    salary_max: Optional[int]
    salary_description: Optional[str]

    location: Optional[str]
    experience_years: Optional[str]
    education: Optional[str]
    skills: Optional[List[str]]

    job_description: Optional[str]
    requirements: Optional[str]
    benefits: Optional[List[str]]

    source_platform: Optional[str]
    source_url: Optional[str]
    source_id: Optional[str]

    published_at: Optional[datetime]
    crawled_at: datetime

    is_duplicate: bool
    is_verified: bool

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        """从 ORM 对象创建：
        - skills / benefits 存的是 JSON 字符串（Text 列），反序列化为 list
        - 兼容旧数据或残留 None
        """
        import json as _json
        data = {}
        for field in cls.model_fields:
            value = getattr(obj, field, None)
            if field in ("skills", "benefits") and isinstance(value, str):
                try:
                    value = _json.loads(value)
                except (_json.JSONDecodeError, TypeError):
                    value = []
            data[field] = value
        return cls(**data)


class JobListingListResponse(BaseModel):
    """招聘信息列表响应Schema"""
    items: List[JobListingResponse]
    total: int
    skip: int
    limit: int


class JobListingFilter(BaseModel):
    """招聘信息筛选条件"""
    company_id: Optional[UUID] = Field(default=None, description="公司ID")
    keyword: Optional[str] = Field(default=None, description="搜索关键词")
    location: Optional[str] = Field(default=None, description="工作地点")
    salary_min: Optional[int] = Field(default=None, description="最低薪资")
    salary_max: Optional[int] = Field(default=None, description="最高薪资")
    source_platform: Optional[str] = Field(default=None, description="来源平台")
    is_verified: Optional[bool] = Field(default=None, description="是否已验证")


class SearchTaskResponse(BaseModel):
    """搜索任务响应Schema"""
    id: UUID
    company_id: UUID
    company_name: Optional[str] = None
    position_config_id: UUID
    position_title: Optional[str] = None

    status: str
    current_step: Optional[str] = None
    progress: Optional[int] = 0
    steps_log: Optional[List[Any]] = None
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    jobs_found: int

    created_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        """从 ORM 对象创建，把 steps_log JSON 字符串反序列化为 list"""
        import json as _json
        data = {}
        for field in cls.model_fields:
            value = getattr(obj, field, None)
            if field == "steps_log" and isinstance(value, str):
                try:
                    value = _json.loads(value)
                except (_json.JSONDecodeError, TypeError):
                    value = []
            data[field] = value
        return cls(**data)


class SearchTaskListResponse(BaseModel):
    """搜索任务列表响应Schema"""
    items: List[SearchTaskResponse]
    total: int
    skip: int
    limit: int


class DashboardStats(BaseModel):
    """仪表盘统计数据"""
    company_count: int
    job_count: int
    today_count: int
    task_count: int


class RunSearchRequest(BaseModel):
    """手动触发搜索请求"""
    company_id: Optional[str] = Field(default=None, description="指定公司ID（可选）")
    position_id: Optional[str] = Field(default=None, description="指定职位配置ID（可选）")
