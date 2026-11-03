import uuid

from redis import Redis


class LocationRepository:
    def __init__(self, redis: Redis, key: str):
        self.redis = redis
        self.key = key

    def save(self, courier_id: uuid.UUID, latitude: float, longitude: float) -> None:
        self.redis.geoadd(self.key, (longitude, latitude, self.member(courier_id)))

    @staticmethod
    def member(courier_id: uuid.UUID) -> str:
        return f"courier-id-{courier_id}"
