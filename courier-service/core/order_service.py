import httpx

from core.config.settings import settings

order_service_client = httpx.Client(
    base_url=settings.ORDER_SERVICE_URL,
    timeout=settings.ORDER_SERVICE_TIMEOUT_SECONDS,
)


def get_order_service_client() -> httpx.Client:
    return order_service_client
