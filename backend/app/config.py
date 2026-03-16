from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # AI Provider Configuration
    ai_provider: str = "gemini"  # "gemini" or "openrouter"

    # Google Gemini
    gemini_api_key: str = ""

    # OpenRouter
    openrouter_api_key: str = ""

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:3001"

    # File Upload
    max_file_size_mb: int = 20
    upload_dir: str = "./uploads"

    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""

    # Data Retention (TTL in seconds)
    file_ttl: int = 3600  # 1 hour
    cache_ttl: int = 3600  # 1 hour

    # Celery Configuration
    celery_broker_url: str = ""  # Auto-generated from redis_url
    celery_result_backend: str = ""  # Auto-generated from redis_url
    celery_task_time_limit: int = 300  # 5 minutes
    celery_result_expires: int = 3600  # 1 hour

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def redis_url(self) -> str:
        """Build Redis URL from components"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def celery_broker(self) -> str:
        """Celery broker URL (Redis DB 0 for queue)"""
        if self.celery_broker_url:
            return self.celery_broker_url
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/0"
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    @property
    def celery_backend(self) -> str:
        """Celery result backend URL (Redis DB 1 for results)"""
        if self.celery_result_backend:
            return self.celery_result_backend
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/1"
        return f"redis://{self.redis_host}:{self.redis_port}/1"


settings = Settings()
