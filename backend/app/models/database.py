"""
数据库连接配置
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # 自动检测断开的连接
    pool_size=10,        # 连接池大小
    max_overflow=20,     # 最大溢出连接数
    echo=settings.DEBUG, # 是否打印SQL语句
)

# 创建会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# 创建模型基类
Base = declarative_base()


def get_db():
    """获取数据库会话（用于FastAPI依赖注入）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库（创建所有表）"""
    # 导入所有模型以确保它们被注册
    from app.models import company, position, job, schedule, email_log

    # 创建所有表
    Base.metadata.create_all(bind=engine)

    # 对已存在的表补齐新增列（SQLite 不会自动 ALTER ADD COLUMN）
    _migrate_search_task_columns(engine)


def _migrate_search_task_columns(engine):
    """轻量迁移：为 search_tasks 表补齐新增的进度字段。

    SQLite 在已有表上不会因 ORM 模型新增字段而自动加列，需手动 ALTER。
    用 PRAGMA table_info 检查列是否存在，缺失才 ADD。
    """
    from sqlalchemy import text, inspect

    inspector = inspect(engine)
    if "search_tasks" not in inspector.get_table_names():
        return  # 表还不存在，create_all 已处理

    existing = {col["name"] for col in inspector.get_columns("search_tasks")}
    # (列名, 列类型 SQL 字面量)
    additions = [
        ("current_step", "VARCHAR(50)"),
        ("progress", "INTEGER DEFAULT 0"),
        ("steps_log", "TEXT"),
        ("position_title", "VARCHAR(100)"),
    ]
    with engine.begin() as conn:
        for col_name, col_type in additions:
            if col_name not in existing:
                conn.execute(
                    text(f"ALTER TABLE search_tasks ADD COLUMN {col_name} {col_type}")
                )

    # job_listings.is_open 新增列
    if "job_listings" in inspector.get_table_names():
        job_existing = {col["name"] for col in inspector.get_columns("job_listings")}
        with engine.begin() as conn:
            if "is_open" not in job_existing:
                conn.execute(
                    text("ALTER TABLE job_listings ADD COLUMN is_open VARCHAR(10) DEFAULT 'unknown'")
                )
