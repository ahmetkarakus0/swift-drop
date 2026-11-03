from typing import Optional

from redis import Redis

from framework.services import Id


class RestaurantLocations:
    """Reads restaurant-service's Redis GEO index. Entries of test restaurants are removed by the
    session cleanup, which finds them through the prefixed restaurant names."""

    def __init__(self, redis: Redis, key: str):
        self.redis = redis
        self.key = key

    def position(self, restaurant_id: Id) -> Optional[tuple[float, float]]:
        """Returns (latitude, longitude), or None if the restaurant has no stored location."""
        stored = self.redis.geopos(self.key, self.member(restaurant_id))[0]
        if stored is None:
            return None
        longitude, latitude = stored
        return latitude, longitude

    @staticmethod
    def member(restaurant_id: Id) -> str:
        return f"restaurant-id-{restaurant_id}"

    def remove(self, restaurant_ids: list[str]) -> int:
        if not restaurant_ids:
            return 0
        return self.redis.zrem(self.key, *(self.member(i) for i in restaurant_ids))
