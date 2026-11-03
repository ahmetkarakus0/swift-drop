import uuid
from typing import Optional

from redis import Redis

from schemas.dispatch_schema import Coordinates

COURIER_MEMBER_PREFIX = "courier-id-"
RESTAURANT_MEMBER_PREFIX = "restaurant-id-"


def courier_id_from_member(member: str) -> uuid.UUID:
    return uuid.UUID(member.removeprefix(COURIER_MEMBER_PREFIX))


class CourierLocationRepository:
    """Reads courier-service's Redis GEO index."""

    def __init__(self, redis: Redis, key: str):
        self.redis = redis
        self.key = key

    def search(self, center: Coordinates, radius_km: float) -> list[tuple[str, float]]:
        """Returns (member, distance in km) pairs within the radius, nearest first."""
        results = self.redis.geosearch(
            self.key,
            longitude=center.longitude,
            latitude=center.latitude,
            radius=radius_km,
            unit="km",
            sort="ASC",
            withdist=True,
        )
        return [(member, float(distance)) for member, distance in results]


class RestaurantLocationRepository:
    """Reads restaurant-service's Redis GEO index."""

    def __init__(self, redis: Redis, key: str):
        self.redis = redis
        self.key = key

    def get(self, restaurant_id: uuid.UUID) -> Optional[Coordinates]:
        stored = self.redis.geopos(self.key, f"{RESTAURANT_MEMBER_PREFIX}{restaurant_id}")[0]
        if stored is None:
            return None
        longitude, latitude = stored
        return Coordinates(latitude=latitude, longitude=longitude)
