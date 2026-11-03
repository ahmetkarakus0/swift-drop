from redis import Redis

from framework.courier_locations import CourierLocations
from framework.services import Id


class CourierAvailability:
    """Reads the online/busy Redis sets used by courier-service and dispatch-service and remembers
    every courier it touched, so their entries can be removed after the case."""

    def __init__(self, redis: Redis, online_key: str, busy_key: str):
        self.redis = redis
        self.online_key = online_key
        self.busy_key = busy_key
        self._members: set[str] = set()

    def is_online(self, courier_id: Id) -> bool:
        return bool(self.redis.sismember(self.online_key, self._member(courier_id)))

    def is_busy(self, courier_id: Id) -> bool:
        return bool(self.redis.sismember(self.busy_key, self._member(courier_id)))

    def mark_busy(self, courier_id: Id) -> None:
        """No service marks couriers busy yet (that comes with assignment), so this writes Redis directly."""
        self.redis.sadd(self.busy_key, self._member(courier_id))

    def _member(self, courier_id: Id) -> str:
        member = CourierLocations.member(courier_id)
        self._members.add(member)
        return member

    def cleanup(self) -> None:
        if self._members:
            self.redis.srem(self.online_key, *self._members)
            self.redis.srem(self.busy_key, *self._members)
