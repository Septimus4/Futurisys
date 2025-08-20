"""Application settings using Pydantic BaseSettings."""

from datetime import datetime
from pathlib import Path

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Database
    database_url: str = Field(
        description="PostgreSQL database URL",
    )

    # API Security
    api_key: str | None = Field(default=None, description="API key for authentication (optional)")

    # Model configuration
    model_artifact_path: str = Field(
        default="model/energy_rf.joblib",
        description="Path to the trained model artifact",
    )

    model_card_path: str = Field(default="model/model_card.json", description="Path to the model card metadata")

    model_name: str = Field(default="sklearn-random-forest", description="Model name identifier")

    model_version: str = Field(
        default_factory=lambda: f"{datetime.now().strftime('%Y%m%d')}_rf_v1",
        description="Model version identifier",
    )

    # Logging
    log_level: str = Field(default="INFO", description="Log level (DEBUG, INFO, WARNING, ERROR)")

    # Performance limits
    max_single_request_size_kb: int = Field(default=16, description="Maximum size for single request in KB")

    max_batch_request_size_mb: int = Field(default=1, description="Maximum size for batch request in MB")

    max_batch_size: int = Field(default=512, description="Maximum number of items in batch request")

    inference_timeout_seconds: int = Field(default=5, description="Timeout for inference operations in seconds")

    # Development
    debug: bool = Field(default=False, description="Enable debug mode")

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        protected_namespaces=(),
        extra="ignore",  # Ignore extra environment variables (e.g., POSTGRES_* for docker-compose)
    )

    def get_model_artifact_path(self) -> Path:
        """Get the absolute path to the model artifact."""
        return Path(self.model_artifact_path).resolve()

    def get_model_card_path(self) -> Path:
        """Get the absolute path to the model card."""
        return Path(self.model_card_path).resolve()

    def is_api_key_enabled(self) -> bool:
        """Check if API key authentication is enabled."""
        return self.api_key is not None and self.api_key.strip() != ""


# Global settings instance
settings = Settings()
