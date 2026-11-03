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
    REDIS_URL: str

    USER_SERVICE_URL: str = "http://127.0.0.1:8000"
    USER_SERVICE_TIMEOUT_SECONDS: float = 5.0

    ORDER_SERVICE_URL: str = "http://127.0.0.1:8002"
    ORDER_SERVICE_TIMEOUT_SECONDS: float = 5.0

    COURIER_LOCATIONS_KEY: str = "courier-locations"
    COURIER_ONLINE_KEY: str = "couriers:online"
    # Must match dispatch-service.
    COURIER_BUSY_KEY: str = "couriers:busy"
    # Must match restaurant-service.
    RESTAURANT_LOCATIONS_KEY: str = "restaurant-locations"

    NEARBY_ORDERS_DEFAULT_RADIUS_KM: float = 5.0
    NEARBY_ORDERS_MAX_RADIUS_KM: float = 20.0


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
