from typing import Optional

from redis import Redis

from framework.services import Id


class CourierLocations:
    """Reads courier-service's Redis GEO index and remembers every courier it was asked about,
    so their entries can be removed after the case (they carry no test prefix)."""

    def __init__(self, redis: Redis, key: str):
        self.redis = redis
        self.key = key
        self._members: set[str] = set()

    def position(self, courier_id: Id) -> Optional[tuple[float, float]]:
        """Returns (latitude, longitude), or None if the courier has no stored location."""
        member = self.member(courier_id)
        self._members.add(member)
        stored = self.redis.geopos(self.key, member)[0]
        if stored is None:
            return None
        longitude, latitude = stored
        return latitude, longitude

    @staticmethod
    def member(courier_id: Id) -> str:
        return f"courier-id-{courier_id}"

    def cleanup(self) -> None:
        if self._members:
            self.redis.zrem(self.key, *self._members)
