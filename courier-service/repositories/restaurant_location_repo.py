import uuid

from redis import Redis

from schemas.location_schema import Coordinates

RESTAURANT_MEMBER_PREFIX = "restaurant-id-"


class RestaurantLocationRepository:
    """Reads restaurant-service's Redis GEO index."""

    def __init__(self, redis: Redis, key: str):
        self.redis = redis
        self.key = key

    def search(self, center: Coordinates, radius_km: float) -> list[tuple[uuid.UUID, float]]:
        """Returns (restaurant id, distance in km) pairs within the radius, nearest first."""
        results = self.redis.geosearch(
            self.key,
            longitude=center.longitude,
            latitude=center.latitude,
            radius=radius_km,
            unit="km",
            sort="ASC",
            withdist=True,
        )
        return [
            (uuid.UUID(member.removeprefix(RESTAURANT_MEMBER_PREFIX)), float(distance))
            for member, distance in results
        ]
