from typing import Iterator

import pytest
from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy.exc import OperationalError

from framework.actors import Actors
from framework.cleanup import cleanup_test_data
from framework.config import Settings, get_settings
from framework.db import Database
from framework.http_client import ApiClient
from framework.services import RestaurantServiceApi, UserServiceApi


@pytest.fixture(scope="session")
def settings() -> Settings:
    return get_settings()


def _connect_db(url: str, name: str) -> Database:
    db = Database(url, name)
    try:
        db.ping()
    except OperationalError as exc:
        pytest.exit(f"Cannot connect to {name}: {exc}. Is `docker compose up -d` running?", returncode=1)
    return db


@pytest.fixture(scope="session")
def user_db(settings: Settings) -> Iterator[Database]:
    db = _connect_db(settings.USER_DB_URL, "user_db")
    yield db
    db.dispose()


@pytest.fixture(scope="session")
def restaurant_db(settings: Settings) -> Iterator[Database]:
    db = _connect_db(settings.RESTAURANT_DB_URL, "restaurant_db")
    yield db
    db.dispose()


@pytest.fixture(scope="session")
def redis_client(settings: Settings) -> Iterator[Redis]:
    client = Redis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=5)
    try:
        client.ping()
    except RedisError as exc:
        pytest.exit(f"Cannot connect to Redis: {exc}", returncode=1)
    yield client
    client.close()


def _service_client(base_url: str, name: str, timeout: float) -> ApiClient:
    client = ApiClient(base_url, name, timeout)
    if not client.is_reachable():
        client.close()
        pytest.exit(f"{name} is not reachable at {base_url}. Start it before running the e2e suite.", returncode=1)
    return client


@pytest.fixture(scope="session")
def user_api(settings: Settings) -> Iterator[UserServiceApi]:
    client = _service_client(settings.USER_SERVICE_URL, "user-service", settings.HTTP_TIMEOUT_SECONDS)
    yield UserServiceApi(client)
    client.close()


@pytest.fixture(scope="session")
def restaurant_api(settings: Settings) -> Iterator[RestaurantServiceApi]:
    client = _service_client(
        settings.RESTAURANT_SERVICE_URL, "restaurant-service", settings.HTTP_TIMEOUT_SECONDS
    )
    yield RestaurantServiceApi(client)
    client.close()


@pytest.fixture(scope="session")
def actors(user_api: UserServiceApi, user_db: Database, settings: Settings) -> Actors:
    return Actors(user_api, user_db, settings)


@pytest.fixture(scope="session", autouse=True)
def _clean_test_data(settings: Settings, user_db: Database, restaurant_db: Database) -> Iterator[None]:
    """Removes leftovers from previous runs before the session and this run's data after it."""
    if settings.KEEP_TEST_DATA:
        yield
        return
    cleanup_test_data(user_db, restaurant_db, settings.TEST_DATA_PREFIX)
    yield
    cleanup_test_data(user_db, restaurant_db, settings.TEST_DATA_PREFIX)
