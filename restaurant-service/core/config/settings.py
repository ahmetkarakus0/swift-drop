from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    POSTGRESQL_URL: str

    USER_SERVICE_URL: str = "http://127.0.0.1:8000"
    USER_SERVICE_TIMEOUT_SECONDS: float = 5.0


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
