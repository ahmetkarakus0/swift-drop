import httpx

from core.config.settings import settings

restaurant_service_client = httpx.Client(
    base_url=settings.RESTAURANT_SERVICE_URL,
    timeout=settings.RESTAURANT_SERVICE_TIMEOUT_SECONDS,
)


def get_restaurant_service_client() -> httpx.Client:
    return restaurant_service_client
