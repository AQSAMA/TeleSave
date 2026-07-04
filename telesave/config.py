from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AnyHttpUrl, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: SecretStr = Field(..., alias="BOT_TOKEN")
    app_env: Literal["development", "production", "test"] = Field("production", alias="APP_ENV")
    log_level: str = Field("INFO", alias="LOG_LEVEL")

    host: str = Field("0.0.0.0", alias="HOST")
    port: int = Field(7860, alias="PORT")

    telegram_api_base_url: str = Field("https://api.telegram.org", alias="TELEGRAM_API_BASE_URL")
    telegram_local_mode: bool = Field(False, alias="TELEGRAM_LOCAL_MODE")

    max_file_size_mb: int = Field(1900, alias="MAX_FILE_SIZE_MB", ge=1, le=2000)
    max_download_seconds: int = Field(900, alias="MAX_DOWNLOAD_SECONDS", ge=10)
    max_concurrent_downloads: int = Field(2, alias="MAX_CONCURRENT_DOWNLOADS", ge=1)
    max_concurrent_downloads_per_user: int = Field(1, alias="MAX_CONCURRENT_DOWNLOADS_PER_USER", ge=1)

    temp_dir: Path = Field(Path("/tmp/telesave"), alias="TEMP_DIR")
    cleanup_after_seconds: int = Field(3600, alias="CLEANUP_AFTER_SECONDS", ge=60)

    ytdlp_cookies_file: Path | None = Field(None, alias="YTDLP_COOKIES_FILE")
    ytdlp_user_agent: str | None = Field(None, alias="YTDLP_USER_AGENT")
    ytdlp_format: str | None = Field(None, alias="YTDLP_FORMAT")
    ytdlp_proxy: AnyHttpUrl | None = Field(None, alias="YTDLP_PROXY")

    direct_download_connect_timeout: float = Field(10.0, alias="DIRECT_DOWNLOAD_CONNECT_TIMEOUT")
    direct_download_read_timeout: float = Field(60.0, alias="DIRECT_DOWNLOAD_READ_TIMEOUT")
    direct_download_max_redirects: int = Field(5, alias="DIRECT_DOWNLOAD_MAX_REDIRECTS", ge=0, le=10)
    direct_download_chunk_size: int = Field(1024 * 1024, alias="DIRECT_DOWNLOAD_CHUNK_SIZE")

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        return value.upper()


@lru_cache
def get_settings() -> Settings:
    return Settings()
