from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "LeadGen Maps Platform"
    api_v1_prefix: str = "/api/v1"
    cors_origins: str = Field(default="http://localhost:3000", alias="BACKEND_CORS_ORIGINS")
    database_url: str = Field(
        default="postgresql+asyncpg://leadgen:leadgen@localhost:5432/leadgen",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    celery_broker_url: str = Field(default="redis://localhost:6379/0", alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/1", alias="CELERY_RESULT_BACKEND")
    secret_key: str = Field(default="change-me", alias="SECRET_KEY")
    playwright_headless: bool = Field(default=True, alias="PLAYWRIGHT_HEADLESS")
    google_sheets_client_secret_path: str | None = Field(default=None, alias="GOOGLE_SHEETS_CLIENT_SECRET_PATH")
    lead_concurrency: int = 6
    max_businesses_per_job: int = 100

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
