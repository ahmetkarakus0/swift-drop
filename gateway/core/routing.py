from core.config.settings import settings

# Path prefix after /api -> upstream service base URL. The longest matching prefix wins,
# so "couriers/location" goes to courier-service while other "couriers/*" paths go to user-service.
ROUTES: dict[str, str] = {
    "auth": settings.USER_SERVICE_URL,
    "users": settings.USER_SERVICE_URL,
    "couriers": settings.USER_SERVICE_URL,
    "couriers/location": settings.COURIER_SERVICE_URL,
    "merchants": settings.USER_SERVICE_URL,
    "restaurants": settings.RESTAURANT_SERVICE_URL,
    "categories": settings.RESTAURANT_SERVICE_URL,
    "items": settings.RESTAURANT_SERVICE_URL,
    "baskets": settings.ORDER_SERVICE_URL,
    "orders": settings.ORDER_SERVICE_URL,
}


def resolve_upstream(path: str) -> str | None:
    segments = path.strip("/").split("/")
    for end in range(len(segments), 0, -1):
        upstream = ROUTES.get("/".join(segments[:end]))
        if upstream is not None:
            return upstream
    return None
