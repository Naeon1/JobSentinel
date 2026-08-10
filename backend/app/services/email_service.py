"""
邮件服务模块

使用 aiosmtplib 异步发送邮件，支持 HTML 模板渲染。
当搜索任务完成后自动发送结果摘要报告。
"""

import smtplib
import asyncio
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.orm import Session

from app.core.config import settings, CST


class EmailService:
    """邮件服务类"""

    def __init__(self, db: Optional[Session] = None):
        self.db = db
        # 模板目录
        template_dir = Path(__file__).parent.parent / "templates"
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )

    async def send_search_report(self, task_results: List[Dict[str, Any]]) -> bool:
        """发送搜索任务报告邮件。

        Args:
            task_results: 搜索任务执行结果列表

        Returns:
            发送是否成功
        """
        if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
            print("[EmailService] SMTP 未配置，跳过邮件发送")
            return False

        if not settings.EMAIL_TO_LIST:
            print("[EmailService] 未配置收件人列表，跳过邮件发送")
            return False

        try:
            subject, html_content = self._build_email_content(task_results)
            return await self._send_email(
                to=settings.EMAIL_TO_LIST,
                subject=subject,
                html=html_content,
            )
        except Exception as e:
            print(f"[EmailService] 发送邮件失败: {e}")
            return False

    def _build_email_content(self, task_results: List[Dict[str, Any]]) -> Tuple[str, str]:
        """构建邮件内容。

        Args:
            task_results: 搜索任务结果列表

        Returns:
            (主题, HTML内容)
        """
        # 统计数据
        total_tasks = len(task_results)
        completed = sum(1 for r in task_results if r.get("status") == "completed")
        failed = sum(1 for r in task_results if r.get("status") == "failed")
        total_jobs = sum(r.get("jobs_found", 0) for r in task_results)

        # 构建模板上下文
        context = {
            "app_name": settings.APP_NAME,
            "current_time": datetime.now(CST).strftime("%Y-%m-%d %H:%M"),
            "total_tasks": total_tasks,
            "completed_tasks": completed,
            "failed_tasks": failed,
            "total_jobs": total_jobs,
            "results": task_results,
        }

        # 渲染模板
        template = self.jinja_env.get_template("email/search_report.html")
        html_content = template.render(**context)

        # 邮件主题
        subject = f"[{settings.APP_NAME}] 招聘信息搜索报告 - 发现 {total_jobs} 条新岗位"

        return subject, html_content

    async def _send_email(self, to: List[str], subject: str, html: str) -> bool:
        """异步发送邮件。

        Args:
            to: 收件人列表
            subject: 邮件主题
            html: HTML内容

        Returns:
            发送是否成功
        """
        # 构建邮件
        msg = MIMEMultipart("alternative")
        msg["From"] = settings.EMAIL_FROM or settings.SMTP_USERNAME
        msg["To"] = ", ".join(to)
        msg["Subject"] = subject

        # 添加 HTML 内容
        msg.attach(MIMEText(html, "html", "utf-8"))

        # 发送邮件
        try:
            # 使用 asyncio 的线程池执行同步操作
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._send_smtp, msg, to)
            print(f"[EmailService] 邮件发送成功，收件人: {to}")
            return True
        except Exception as e:
            print(f"[EmailService] SMTP 发送失败: {e}")
            return False

    def _send_smtp(self, msg: MIMEMultipart, to: List[str]) -> None:
        """同步发送 SMTP 邮件（在线程池中运行）。"""
        smtp_class = smtplib.SMTP_SSL if settings.SMTP_PORT == 465 else smtplib.SMTP
        with smtp_class(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as server:
            # 587 使用 STARTTLS；465 使用连接建立时的 SSL。
            if settings.SMTP_PORT == 587:
                server.starttls()
            # 登录
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            # 发送
            server.send_message(msg, to_addrs=to)

    def send_test_email(self, to: List[str]) -> Tuple[bool, str]:
        """发送测试邮件（同步方法）。

        Args:
            to: 收件人列表

        Returns:
            (成功与否, 消息)
        """
        if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
            return False, "SMTP 未配置，请检查 SMTP_USERNAME 和 SMTP_PASSWORD"

        try:
            subject = f"[{settings.APP_NAME}] 邮件配置测试"
            html = f"""
            <html>
            <body>
                <h2>{settings.APP_NAME} 邮件配置测试</h2>
                <p>这是一封测试邮件，用于验证邮件配置是否正确。</p>
                <p>发送时间：{datetime.now(CST).strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>如果您收到此邮件，说明邮件服务配置正确。</p>
            </body>
            </html>
            """

            msg = MIMEMultipart("alternative")
            msg["From"] = settings.EMAIL_FROM or settings.SMTP_USERNAME
            msg["To"] = ", ".join(to)
            msg["Subject"] = subject
            msg.attach(MIMEText(html, "html", "utf-8"))

            self._send_smtp(msg, to)
            return True, f"测试邮件发送成功，收件人: {', '.join(to)}"
        except Exception as e:
            return False, f"发送失败: {str(e)}"
