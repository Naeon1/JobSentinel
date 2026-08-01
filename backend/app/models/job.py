"""
招聘信息模型
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, ForeignKey
from datetime import datetime
import uuid
import json

from app.models.database import Base


class SearchTask(Base):
    """搜索任务模型"""

    __tablename__ = "search_tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(
        String(36),
        ForeignKey("companies.id"),
        comment="公司ID"
    )
    position_config_id = Column(
        String(36),
        ForeignKey("position_configs.id"),
        comment="职位配置ID"
    )
    status = Column(
        String(20),
        default="pending",
        comment="任务状态: pending/planning/searching/extracting/completed/failed"
    )
    current_step = Column(
        String(50),
        comment="当前阶段: planning/searching/extracting/done"
    )
    progress = Column(Integer, default=0, comment="进度百分比 0-100")
    steps_log = Column(Text, comment="步骤日志（JSON数组: [{step,status,message,timestamp}]）")
    position_title = Column(String(100), comment="职位名（冗余，供前端列表展示）")
    started_at = Column(DateTime, comment="开始时间")
    completed_at = Column(DateTime, comment="完成时间")
    error_message = Column(Text, comment="错误信息")
    jobs_found = Column(Integer, default=0, comment="找到的职位数")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    def __repr__(self):
        return f"<SearchTask(id={self.id}, status='{self.status}')>"

    def to_dict(self):
        """转换为字典"""
        steps_log = []
        if self.steps_log:
            try:
                steps_log = json.loads(self.steps_log)
            except (json.JSONDecodeError, TypeError):
                steps_log = []

        return {
            "id": self.id,
            "company_id": self.company_id,
            "position_config_id": self.position_config_id,
            "status": self.status,
            "current_step": self.current_step,
            "progress": self.progress,
            "steps_log": steps_log,
            "position_title": self.position_title,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "jobs_found": self.jobs_found,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class JobListing(Base):
    """招聘信息模型"""

    __tablename__ = "job_listings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(
        String(36),
        ForeignKey("search_tasks.id"),
        comment="任务ID"
    )
    company_id = Column(
        String(36),
        ForeignKey("companies.id"),
        comment="公司ID"
    )

    # 基本信息
    job_title = Column(String(200), nullable=False, comment="职位名称")
    is_open = Column(String(10), default="unknown", comment="是否在招: true/false/unknown")
    salary_min = Column(Integer, comment="最低薪资（元/月）")
    salary_max = Column(Integer, comment="最高薪资（元/月）")
    salary_description = Column(String(100), comment="原始薪资描述")

    # 要求
    location = Column(String(100), comment="工作地点")
    experience_years = Column(String(50), comment="经验要求")
    education = Column(String(50), comment="学历要求")
    skills = Column(Text, comment="技能要求（JSON格式）")

    # 描述
    job_description = Column(Text, comment="职位描述")
    requirements = Column(Text, comment="任职要求")
    benefits = Column(Text, comment="福利待遇（JSON格式）")

    # 来源信息
    source_platform = Column(String(50), comment="来源平台")
    source_url = Column(String(500), comment="原始链接")
    source_id = Column(String(100), comment="平台上的ID")

    # 时间
    published_at = Column(DateTime, comment="发布时间")
    crawled_at = Column(DateTime, default=datetime.utcnow, comment="抓取时间")

    # 状态
    is_duplicate = Column(Boolean, default=False, comment="是否重复")
    is_verified = Column(Boolean, default=False, comment="是否人工确认")

    def __repr__(self):
        return f"<JobListing(id={self.id}, title='{self.job_title}')>"

    def to_dict(self):
        """转换为字典"""
        skills = []
        benefits = []

        if self.skills:
            try:
                skills = json.loads(self.skills)
            except (json.JSONDecodeError, TypeError):
                skills = []

        if self.benefits:
            try:
                benefits = json.loads(self.benefits)
            except (json.JSONDecodeError, TypeError):
                benefits = []

        return {
            "id": self.id,
            "task_id": self.task_id,
            "company_id": self.company_id,
            "job_title": self.job_title,
            "is_open": self.is_open,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "salary_description": self.salary_description,
            "location": self.location,
            "experience_years": self.experience_years,
            "education": self.education,
            "skills": skills,
            "job_description": self.job_description,
            "requirements": self.requirements,
            "benefits": benefits,
            "source_platform": self.source_platform,
            "source_url": self.source_url,
            "source_id": self.source_id,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "crawled_at": self.crawled_at.isoformat() if self.crawled_at else None,
            "is_duplicate": self.is_duplicate,
            "is_verified": self.is_verified,
        }
