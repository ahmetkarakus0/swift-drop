import uuid
from typing import Optional

from redis import Redis

from schemas.location_schema import Coordinates


class LocationRepository:
    def __init__(self, redis: Redis, key: str):
        self.redis = redis
        self.key = key

    def save(self, courier_id: uuid.UUID, latitude: float, longitude: float) -> None:
        self.redis.geoadd(self.key, (longitude, latitude, self.member(courier_id)))

    def get(self, courier_id: uuid.UUID) -> Optional[Coordinates]:
        stored = self.redis.geopos(self.key, self.member(courier_id))[0]
        if stored is None:
            return None
        longitude, latitude = stored
        return Coordinates(latitude=latitude, longitude=longitude)

    @staticmethod
    def member(courier_id: uuid.UUID) -> str:
        return f"courier-id-{courier_id}"
