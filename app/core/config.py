"""
配置管理模块
使用 Pydantic Settings 进行配置管理，支持环境变量和 .env 文件
"""
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类"""

    # ========== 应用基础配置 ==========
    APP_NAME: str = Field(default="Konus Mate API", description="应用名称")
    APP_VERSION: str = Field(default="1.0.0", description="应用版本")
    DEBUG: bool = Field(default=False, description="调试模式")
    API_PREFIX: str = Field(default="/api/v1", description="API 路径前缀")

    # ========== 服务器配置 ==========
    HOST: str = Field(default="0.0.0.0", description="服务器地址")
    PORT: int = Field(default=8000, description="服务器端口")

    # ========== 数据库配置 ==========
    # PostgreSQL 数据库连接信息
    # DB_HOST: str = Field(default="89.208.242.21", description="数据库主机")
    # DB_PORT: int = Field(default=15432, description="数据库端口")
    DB_HOST: str = Field(default="192.168.2.7", description="数据库主机")
    DB_PORT: int = Field(default=5432, description="数据库端口")
    DB_NAME: str = Field(default="mate_db", description="数据库名称")
    DB_USER: str = Field(default="konus", description="数据库用户")
    DB_PASSWORD: str = Field(default="LGligang", description="数据库密码")

    # 数据库连接池配置
    DB_POOL_SIZE: int = Field(default=20, description="连接池大小")
    DB_MAX_OVERFLOW: int = Field(default=30, description="连接池最大溢出")
    DB_POOL_TIMEOUT: int = Field(default=30, description="连接池超时时间")
    DB_POOL_RECYCLE: int = Field(default=3600, description="连接回收时间（秒）")

    # ========== AI/LLM 配置 ==========
    # 智谱 AI API 配置
    ZHIPU_API_KEY: str = Field(default="", description="智谱 AI API Key")

    # DeepSeek API 配置
    DEEPSEEK_API_KEY: str = Field(default="", description="DeepSeek API Key")

    # LiteLLM 配置
    LITELLM_MODEL: str = Field(default="zhipuai/glm-4", description="LiteLLM 模型名称")
    LITELLM_TEMPERATURE: float = Field(default=0.7, description="LLM 温度参数")
    LITELLM_MAX_TOKENS: int = Field(default=2000, description="LLM 最大 token 数")
    LITELLM_TIMEOUT: int = Field(default=60, description="LLM 请求超时时间")

    # ========== LangChain/LangGraph 配置 ==========
    LANGCHAIN_TRACING_V2: bool = Field(default=False, description="启用 LangChain 追踪")
    LANGCHAIN_API_KEY: Optional[str] = Field(default=None, description="LangChain API Key")
    LANGCHAIN_PROJECT: str = Field(default="konus-mate", description="LangChain 项目名称")

    # ========== 缓存配置 ==========
    REDIS_HOST: Optional[str] = Field(default=None, description="Redis 主机")
    REDIS_PORT: int = Field(default=6379, description="Redis 端口")
    REDIS_DB: int = Field(default=0, description="Redis 数据库")
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis 密码")

    # ========== 日志配置 ==========
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    LOG_FILE: Optional[str] = Field(default=None, description="日志文件路径")

    # ========== 安全配置 ==========
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        description="JWT 密钥（生产环境必须修改）"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24 * 7, description="访问令牌过期时间")

    # ========== CORS 配置 ==========
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="允许的跨域来源"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """解析 CORS 配置"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def database_url(self) -> str:
        """生成数据库连接 URL"""
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def sync_database_url(self) -> str:
        """生成同步数据库连接 URL（用于初始化脚本）"""
        return f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


# 全局配置实例
settings = Settings()
