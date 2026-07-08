from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Core application settings loaded from environment variables."""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = "dev-secret-key-statmind-ai"

    # Execution Sandbox
    MAX_EXECUTION_MEMORY_MB: int = 512
    MAX_EXECUTION_TIME_SECONDS: int = 60
    SANDBOX_ENABLED: bool = True

    # OpenAI API
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_MINI_MODEL: str = "gpt-4o-mini"

    # Database & Cache
    DATABASE_URL: str = "postgresql://statmind:statmindpass@localhost:5432/statmind_db"
    REDIS_URL: str = "redis://localhost:6379/0"


settings = Settings()
