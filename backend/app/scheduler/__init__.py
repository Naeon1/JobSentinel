"""
定时任务调度器

基于 APScheduler 的 BackgroundScheduler，按 cron 表达式定期触发
"全部启用公司 × 启用职位"的批量搜索。

调度器在应用 lifespan 启动时初始化，关闭时停止。运行时若用户通过
 /api/schedules/current 修改了 cron 或启停状态，调用 reschedule() 即可
 热更新，无需重启进程。
"""

import threading
import asyncio
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.models.database import SessionLocal
from app.models.job import SearchTask
from app.services.search_service import SearchService
from app.services.email_service import EmailService


# 单例调度器（进程内唯一）
_scheduler: Optional[BackgroundScheduler] = None
# job 的固定 id，便于 reschedule 时定位
_JOB_ID = "scheduled_batch_search"
# 线程锁，保证 init / reschedule / shutdown 不会并发踩踏
_lock = threading.Lock()


def _run_scheduled_batch() -> None:
    """调度器触发的入口：执行一次全量批量搜索。

    复用 SearchService.prepare_batch_tasks + run_existing_tasks 的两段式
    流程（与手动触发的 /api/tasks/run 后台逻辑一致），保证定时任务产出的
    SearchTask 记录与手动触发的同构，前端可视化和去重逻辑无需区分来源。
    """
    db = SessionLocal()
    try:
        print("[Scheduler] 定时任务触发，开始批量搜索...")
        search_service = SearchService(db)
        tasks = search_service.prepare_batch_tasks()
        if not tasks:
            print("[Scheduler] 没有可执行的公司×职位组合，跳过本次")
            return
        task_ids = [str(t.id) for t in tasks]
        results = search_service.run_existing_tasks(task_ids)
        ok = sum(1 for r in results if r.get("status") == "completed")
        print(f"[Scheduler] 本次批量搜索完成：成功 {ok}/{len(results)}")

        # 发送邮件报告
        if results:
            _send_email_report(results)
    except Exception as e:
        import traceback
        traceback.print_exc()
        # 兜底：把本次可能遗留的 running 任务标 failed
        try:
            zombies = db.query(SearchTask).filter(
                SearchTask.status.in_(["running", "planning", "searching", "extracting"])
            ).all()
            for t in zombies:
                t.status = "failed"
                t.error_message = f"定时任务执行异常: {e}"
            if zombies:
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


def _build_trigger() -> CronTrigger:
    """根据当前 settings.SCHEDULE_CRON 构建 CronTrigger。"""
    return CronTrigger.from_crontab(settings.SCHEDULE_CRON)


def init_scheduler() -> None:
    """初始化并启动调度器（应用启动时调用一次）。"""
    global _scheduler
    with _lock:
        if _scheduler is not None:
            return  # 已初始化，幂等
        _scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
        _scheduler.start()
        print("[Scheduler] 调度器已启动")
        _apply_job()


def _apply_job() -> None:
    """根据 settings.SCHEDULE_ENABLED 决定添加或移除定时 job。"""
    if _scheduler is None:
        return
    # 先清掉旧 job（若存在），避免重复
    try:
        _scheduler.remove_job(_JOB_ID)
    except Exception:
        pass

    if not settings.SCHEDULE_ENABLED:
        print("[Scheduler] 定时任务未启用")
        return

    try:
        _scheduler.add_job(
            _run_scheduled_batch,
            trigger=_build_trigger(),
            id=_JOB_ID,
            replace_existing=True,
            misfire_grace_time=3600,  # 错过-fire 容忍 1 小时（进程重启补跑）
            coalesce=True,            # 多次错过只补跑一次
        )
        print(f"[Scheduler] 定时任务已注册：cron='{settings.SCHEDULE_CRON}'")
    except Exception as e:
        print(f"[Scheduler] 注册定时任务失败：{e}")


def reschedule() -> None:
    """配置热更新：用户改了 cron 或启停后调用，立即重排定时 job。"""
    with _lock:
        if _scheduler is None:
            return
        _apply_job()


def get_next_run_time() -> Optional[str]:
    """返回下次执行的 ISO 时间字符串；调度器未运行或未启用时返回 None。"""
    with _lock:
        if _scheduler is None:
            return None
        job = _scheduler.get_job(_JOB_ID)
        if job is None:
            return None
        try:
            next_dt = job.next_run_time
        except Exception:
            return None
        if next_dt is None:
            return None
        # APScheduler 用的是带 tz 的 datetime，isoformat() 会带 +08:00
        return next_dt.isoformat()


def shutdown_scheduler() -> None:
    """关闭调度器（应用退出时调用）。"""
    global _scheduler
    with _lock:
        if _scheduler is None:
            return
        try:
            _scheduler.shutdown(wait=False)
            print("[Scheduler] 调度器已停止")
        except Exception as e:
            print(f"[Scheduler] 停止调度器时出错：{e}")
        finally:
            _scheduler = None


def _send_email_report(task_results: list) -> None:
    """发送邮件报告（在独立线程中运行异步代码）。"""
    if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
        return
    if not settings.EMAIL_TO_LIST:
        return

    try:
        email_service = EmailService()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(email_service.send_search_report(task_results))
        loop.close()
    except Exception as e:
        print(f"[Scheduler] 发送邮件报告失败: {e}")
