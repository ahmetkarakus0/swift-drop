import uuid

from redis import Redis


class RestaurantLocationRepository:
    def __init__(self, redis: Redis, key: str):
        self.redis = redis
        self.key = key

    def save(self, restaurant_id: uuid.UUID, latitude: float, longitude: float) -> None:
        self.redis.geoadd(self.key, (longitude, latitude, self._member(restaurant_id)))

    def delete(self, restaurant_id: uuid.UUID) -> None:
        self.redis.zrem(self.key, self._member(restaurant_id))

    @staticmethod
    def _member(restaurant_id: uuid.UUID) -> str:
        return f"restaurant-id-{restaurant_id}"
