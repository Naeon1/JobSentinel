"""
应用配置管理
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import validator


class Settings(BaseSettings):
    """应用设置"""

    # 应用配置
    APP_NAME: str = "JobSentinel"
    DEBUG: bool = False
    SECRET_KEY: str = "your-secret-key-change-in-production"

    # 数据库配置
    DATABASE_URL: str = ""

    # ==================== AI服务配置 ====================
    # API类型：openai / anthropic / custom
    LLM_PROVIDER: str = "openai"

    # 自定义API地址（兼容OpenAI格式的服务）
    # 示例：
    # - Ollama: http://localhost:11434/v1
    # - vLLM: http://localhost:8000/v1
    # - 第三方代理: https://api.example.com/v1
    # - OpenAI官方: https://api.openai.com/v1
    LLM_API_BASE_URL: str = "https://api.openai.com/v1"

    # API密钥
    LLM_API_KEY: str = ""

    # 模型名称
    # 示例：
    # - OpenAI: gpt-4o, gpt-4-turbo, gpt-3.5-turbo
    # - Ollama: qwen2:7b, llama3:8b, deepseek-coder:7b
    # - Claude: claude-3-5-sonnet-20241022
    LLM_MODEL_NAME: str = "gpt-4o"

    # 是否使用Anthropic格式（仅当LLM_PROVIDER=anthropic时有效）
    LLM_USE_ANTHROPIC_FORMAT: bool = False

    # 兼容旧配置（可选）
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # 搜索API配置
    SERPAPI_KEY: Optional[str] = None

    # 邮件配置
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: Optional[str] = None
    EMAIL_TO_LIST: List[str] = []

    # CORS配置
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    # 定时任务配置
    SCHEDULE_CRON: str = "0 9 * * *"
    SCHEDULE_ENABLED: bool = False

    # 搜索配置
    SEARCH_RESULTS_LIMIT: int = 10
    SEARCH_DELAY: int = 2
    USE_PROXY: bool = False
    PROXY_URL: Optional[str] = None

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"

    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        """解析CORS配置"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @validator("EMAIL_TO_LIST", pre=True)
    def parse_email_list(cls, v):
        """解析邮件列表"""
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except:
                return [email.strip() for email in v.split(",")]
        return v

    def get_llm_api_key(self) -> str:
        """获取LLM API密钥"""
        # 优先使用新的配置
        if self.LLM_API_KEY:
            return self.LLM_API_KEY
        # 兼容旧配置
        if self.LLM_PROVIDER == "anthropic" and self.ANTHROPIC_API_KEY:
            return self.ANTHROPIC_API_KEY
        if self.OPENAI_API_KEY:
            return self.OPENAI_API_KEY
        return ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 创建全局设置实例
settings = Settings()


def get_settings() -> Settings:
    """获取设置实例"""
    return settings
