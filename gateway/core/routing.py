from core.config.settings import settings

# First path segment after /api -> upstream service base URL.
ROUTES: dict[str, str] = {
    "auth": settings.USER_SERVICE_URL,
    "couriers": settings.USER_SERVICE_URL,
    "merchants": settings.USER_SERVICE_URL,
    "restaurants": settings.RESTAURANT_SERVICE_URL,
    "categories": settings.RESTAURANT_SERVICE_URL,
    "items": settings.RESTAURANT_SERVICE_URL,
}


def resolve_upstream(path: str) -> str | None:
    resource = path.strip("/").split("/", 1)[0]
    return ROUTES.get(resource)
