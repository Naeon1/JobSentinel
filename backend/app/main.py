"""
JobSentinel - FastAPI应用入口
"""

import sys
import io

# Windows 中文控制台默认 GBK 编码，emoji 字符会触发 UnicodeEncodeError，
# 这里把标准输出/错误流强制重置为 UTF-8。
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
else:  # 兼容旧版本 Python
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.models.database import init_db, SessionLocal
from app.models.job import SearchTask
from app.api import companies, positions, jobs, tasks, schedules, email
from app.scheduler import init_scheduler, shutdown_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    print("🚀 正在启动应用...")
    init_db()
    print("✅ 数据库初始化完成")

    # 把上次进程中断留下的"僵尸"任务（仍在 running/planning）标记为 failed
    _cleanup_zombie_tasks()

    # 启动定时任务调度器（按 settings.SCHEDULE_CRON / SCHEDULE_ENABLED 注册首个 job）
    init_scheduler()

    yield

    # 关闭时执行
    print("👋 应用正在关闭...")
    shutdown_scheduler()


def _cleanup_zombie_tasks():
    """启动时清理上次未结束的任务：将 running/planning 状态的任务标为 failed。"""
    db = SessionLocal()
    try:
        zombies = db.query(SearchTask).filter(
            SearchTask.status.in_(["running", "planning", "searching", "extracting"])
        ).all()
        for t in zombies:
            t.status = "failed"
            t.error_message = "进程中断，任务未正常结束"
            t.completed_at = None
        if zombies:
            db.commit()
            print(f"🧹 清理了 {len(zombies)} 个未结束任务")
    except Exception as e:
        print(f"清理僵尸任务出错: {e}")
    finally:
        db.close()


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    description="JobSentinel - 基于AI的招聘信息自动搜索和分析系统",
    version="1.0.0",
    lifespan=lifespan,
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(companies.router)
app.include_router(positions.router)
app.include_router(jobs.router)
app.include_router(tasks.router)
app.include_router(schedules.router)
app.include_router(email.router)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "欢迎使用 JobSentinel",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
