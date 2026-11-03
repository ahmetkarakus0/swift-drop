from typing import Iterator

import pytest
from confluent_kafka import KafkaException
from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy.exc import OperationalError

from framework.actors import Actors
from framework.cleanup import cleanup_test_data
from framework.config import Settings, get_settings
from framework.courier_availability import CourierAvailability
from framework.courier_locations import CourierLocations
from framework.db import Database
from framework.http_client import ApiClient
from framework.menus import Menus
from framework.order_events import OrderEvents
from framework.restaurant_locations import RestaurantLocations
from framework.services import CourierServiceApi, OrderServiceApi, RestaurantServiceApi, UserServiceApi


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
def order_db(settings: Settings) -> Iterator[Database]:
    db = _connect_db(settings.ORDER_DB_URL, "order_db")
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


def _service_client(base_url: str, name: str, timeout: float, probe_path: str = "/openapi.json") -> ApiClient:
    client = ApiClient(base_url, name, timeout)
    if not client.is_reachable(probe_path):
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
def order_api(settings: Settings) -> Iterator[OrderServiceApi]:
    """Only requested by order cases, so the rest of the suite runs without order-service."""
    client = _service_client(settings.ORDER_SERVICE_URL, "order-service", settings.HTTP_TIMEOUT_SECONDS)
    yield OrderServiceApi(client)
    client.close()


@pytest.fixture(scope="session")
def courier_api(settings: Settings) -> Iterator[CourierServiceApi]:
    """Only requested by courier cases, so the rest of the suite runs without courier-service."""
    client = _service_client(settings.COURIER_SERVICE_URL, "courier-service", settings.HTTP_TIMEOUT_SECONDS)
    yield CourierServiceApi(client)
    client.close()


@pytest.fixture(scope="session")
def gateway_client(settings: Settings) -> Iterator[ApiClient]:
    """Only requested by gateway cases, so the rest of the suite runs without the gateway."""
    client = _service_client(settings.GATEWAY_URL, "gateway", settings.HTTP_TIMEOUT_SECONDS, "/health")
    yield client
    client.close()


@pytest.fixture(scope="session")
def gateway_user_api(gateway_client: ApiClient) -> UserServiceApi:
    return UserServiceApi(gateway_client)


@pytest.fixture(scope="session")
def gateway_courier_api(gateway_client: ApiClient) -> CourierServiceApi:
    return CourierServiceApi(gateway_client)


@pytest.fixture(scope="session")
def gateway_restaurant_api(gateway_client: ApiClient) -> RestaurantServiceApi:
    return RestaurantServiceApi(gateway_client)


@pytest.fixture(scope="session")
def gateway_order_api(gateway_client: ApiClient) -> OrderServiceApi:
    return OrderServiceApi(gateway_client)


@pytest.fixture(scope="session")
def gateway_actors(gateway_user_api: UserServiceApi, user_db: Database, settings: Settings) -> Actors:
    return Actors(gateway_user_api, user_db, settings)


@pytest.fixture(scope="session")
def gateway_menus(gateway_restaurant_api: RestaurantServiceApi) -> Menus:
    return Menus(gateway_restaurant_api)


@pytest.fixture
def courier_locations(redis_client: Redis, settings: Settings) -> Iterator[CourierLocations]:
    locations = CourierLocations(redis_client, settings.COURIER_LOCATIONS_KEY)
    yield locations
    if not settings.KEEP_TEST_DATA:
        locations.cleanup()


@pytest.fixture
def courier_availability(redis_client: Redis, settings: Settings) -> Iterator[CourierAvailability]:
    availability = CourierAvailability(redis_client, settings.COURIER_ONLINE_KEY, settings.COURIER_BUSY_KEY)
    yield availability
    if not settings.KEEP_TEST_DATA:
        availability.cleanup()


@pytest.fixture(scope="session")
def restaurant_locations(redis_client: Redis, settings: Settings) -> RestaurantLocations:
    return RestaurantLocations(redis_client, settings.RESTAURANT_LOCATIONS_KEY)


def _topic_events(settings: Settings, topic: str) -> OrderEvents:
    try:
        return OrderEvents(settings.KAFKA_BOOTSTRAP_SERVERS, topic, settings.KAFKA_TIMEOUT_SECONDS)
    except KafkaException as exc:
        pytest.fail(f"Cannot read {topic} from Kafka: {exc}")


@pytest.fixture
def order_events(settings: Settings) -> Iterator[OrderEvents]:
    """Only requested by event cases, so the rest of the suite runs without Kafka."""
    events = _topic_events(settings, settings.KAFKA_ORDER_EVENTS_TOPIC)
    yield events
    events.close()


@pytest.fixture(scope="session")
def dispatch_service(settings: Settings) -> None:
    """dispatch-service has no endpoints the cases call; this only checks that it is running."""
    _service_client(settings.DISPATCH_SERVICE_URL, "dispatch-service", settings.HTTP_TIMEOUT_SECONDS).close()


@pytest.fixture
def dispatch_events(settings: Settings, dispatch_service: None) -> Iterator[OrderEvents]:
    """dispatch-service's events, keyed by order id. Only requested by dispatch cases."""
    events = _topic_events(settings, settings.KAFKA_DISPATCH_EVENTS_TOPIC)
    yield events
    events.close()


@pytest.fixture(scope="session")
def actors(user_api: UserServiceApi, user_db: Database, settings: Settings) -> Actors:
    return Actors(user_api, user_db, settings)


@pytest.fixture(scope="session")
def menus(restaurant_api: RestaurantServiceApi) -> Menus:
    return Menus(restaurant_api)


@pytest.fixture(scope="session", autouse=True)
def _clean_test_data(
    settings: Settings,
    user_db: Database,
    restaurant_db: Database,
    order_db: Database,
    restaurant_locations: RestaurantLocations,
) -> Iterator[None]:
    """Removes leftovers from previous runs before the session and this run's data after it."""
    if settings.KEEP_TEST_DATA:
        yield
        return
    cleanup_test_data(user_db, restaurant_db, order_db, restaurant_locations, settings.TEST_DATA_PREFIX)
    yield
    cleanup_test_data(user_db, restaurant_db, order_db, restaurant_locations, settings.TEST_DATA_PREFIX)
