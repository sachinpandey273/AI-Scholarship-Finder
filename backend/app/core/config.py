from functools import lru_cache
from pathlib import Path
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    environment: str = "development"
    database_url: str = "postgresql+psycopg://scholarship:scholarship@postgres:5432/scholarship"
    redis_url: str = "redis://redis:6379/0"
    jwt_issuer: str = ""
    jwt_audience: str = ""
    jwt_public_key: str = ""
    allowed_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    upload_max_bytes: int = 10 * 1024 * 1024
    upload_storage_path: Path = Path("/var/lib/scholarship/uploads")
    upload_retention_days: int = 30
    workflow_max_attempts: int = 3

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_render_postgres_url(cls, value: str) -> str:
        # Render exposes PostgreSQL URLs without SQLAlchemy's driver segment.
        return value.replace("postgresql://", "postgresql+psycopg://", 1)

    def validate_runtime(self) -> None:
        if self.environment == "production" and not (self.jwt_issuer and self.jwt_audience and self.jwt_public_key):
            raise RuntimeError("Production requires JWT_ISSUER, JWT_AUDIENCE, and JWT_PUBLIC_KEY.")


@lru_cache
def get_settings() -> Settings:
    return Settings()
