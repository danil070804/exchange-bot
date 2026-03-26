from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    """Application configuration loaded from environment or .env."""

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = Field(default="development", alias="ENV")
    database_url: str = Field(
        default="postgresql+psycopg2://exchange:exchange@localhost:5432/exchange",
        alias="DATABASE_URL",
    )
    redis_url: str | None = Field(default=None, alias="REDIS_URL")
    timezone: str = Field(default="Europe/Kyiv", alias="TIMEZONE")

    bot_internal_token: str | None = Field(default=None, alias="BACKEND_BOT_TOKEN")
    admin_api_token: str | None = Field(default=None, alias="ADMIN_API_TOKEN")
    public_base_url: str | None = Field(default=None, alias="PUBLIC_BASE_URL")

    enable_echo_sql: bool = Field(default=False, alias="ECHO_SQL")


settings = Settings()
