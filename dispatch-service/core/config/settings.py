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

    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_FLUSH_TIMEOUT_SECONDS: float = 10.0
    KAFKA_ORDER_EVENTS_TOPIC: str = "order-events"
    KAFKA_DISPATCH_EVENTS_TOPIC: str = "dispatch-events"
    KAFKA_CONSUMER_GROUP_ID: str = "dispatch-service"
    KAFKA_AUTO_OFFSET_RESET: str = "earliest"

    # Must match courier-service and restaurant-service.
    COURIER_LOCATIONS_KEY: str = "courier-locations"
    COURIER_ONLINE_KEY: str = "couriers:online"
    COURIER_BUSY_KEY: str = "couriers:busy"
    RESTAURANT_LOCATIONS_KEY: str = "restaurant-locations"

    # Searched in order; the first radius with an available courier wins.
    COURIER_SEARCH_RADII_KM: list[float] = [2.0, 5.0]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
