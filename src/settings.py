from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        protected_namespaces=("settings_",),
        populate_by_name=True,
    )

    app_name: str = "zero-shot-api"
    app_version: str = "0.1.0"
    database_url: str = Field("sqlite+pysqlite:///:memory:", alias="DATABASE_URL")
    api_key: str | None = Field(None, alias="API_KEY")
    model_name: str = Field("facebook/bart-large-mnli", alias="MODEL_NAME")
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    inference_timeout_seconds: int = Field(10, alias="INFERENCE_TIMEOUT_SECONDS")


@lru_cache
def get_settings() -> Settings:  # pragma: no cover - trivial
    # Rely on environment variables (aliases) so simple call is fine.
    return Settings()  # type: ignore[call-arg]
