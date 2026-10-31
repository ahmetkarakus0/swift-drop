import httpx

from core.config.settings import settings

user_service_client = httpx.Client(
    base_url=settings.USER_SERVICE_URL,
    timeout=settings.USER_SERVICE_TIMEOUT_SECONDS,
)


def get_user_service_client() -> httpx.Client:
    return user_service_client
