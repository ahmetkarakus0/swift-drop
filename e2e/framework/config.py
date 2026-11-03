from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    USER_SERVICE_URL: str = "http://127.0.0.1:8000"
    RESTAURANT_SERVICE_URL: str = "http://127.0.0.1:8001"
    ORDER_SERVICE_URL: str = "http://127.0.0.1:8002"
    COURIER_SERVICE_URL: str = "http://127.0.0.1:8003"
    DISPATCH_SERVICE_URL: str = "http://127.0.0.1:8004"
    GATEWAY_URL: str = "http://127.0.0.1:8080"
    HTTP_TIMEOUT_SECONDS: float = 10.0

    USER_DB_URL: str
    RESTAURANT_DB_URL: str
    ORDER_DB_URL: str
    REDIS_URL: str
    COURIER_LOCATIONS_KEY: str = "courier-locations"
    COURIER_ONLINE_KEY: str = "couriers:online"
    COURIER_BUSY_KEY: str = "couriers:busy"
    RESTAURANT_LOCATIONS_KEY: str = "restaurant-locations"
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_ORDER_EVENTS_TOPIC: str = "order-events"
    KAFKA_DISPATCH_EVENTS_TOPIC: str = "dispatch-events"
    KAFKA_TIMEOUT_SECONDS: float = 10.0

    TEST_DATA_PREFIX: str = "e2e_test"
    TEST_EMAIL_DOMAIN: str = "e2e.swiftdrop.test"
    DEFAULT_PASSWORD: str = "Password123!"

    KEEP_TEST_DATA: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
