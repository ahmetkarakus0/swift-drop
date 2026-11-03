import enum
import uuid

from redis import Redis

from repositories.location_repo import LocationRepository

# KEYS[1] = online set, KEYS[2] = busy set, ARGV[1] = courier member.
_CLAIM_BUSY_SCRIPT = """
if redis.call('SISMEMBER', KEYS[1], ARGV[1]) == 0 then
    return -1
end
return redis.call('SADD', KEYS[2], ARGV[1])
"""


class BusyClaim(enum.Enum):
    CLAIMED = "claimed"
    OFFLINE = "offline"
    ALREADY_BUSY = "already_busy"


class AvailabilityRepository:
    """Online and busy couriers are Redis sets, using the same members as the location index."""

    def __init__(self, redis: Redis, online_key: str, busy_key: str):
        self.redis = redis
        self.online_key = online_key
        self.busy_key = busy_key

    def set_online(self, courier_id: uuid.UUID) -> None:
        self.redis.sadd(self.online_key, LocationRepository.member(courier_id))

    def set_offline(self, courier_id: uuid.UUID) -> None:
        self.redis.srem(self.online_key, LocationRepository.member(courier_id))

    def claim_busy(self, courier_id: uuid.UUID) -> BusyClaim:
        """Atomically marks an online courier busy."""
        result = self.redis.eval(
            _CLAIM_BUSY_SCRIPT,
            2,
            self.online_key,
            self.busy_key,
            LocationRepository.member(courier_id),
        )
        if result == -1:
            return BusyClaim.OFFLINE
        return BusyClaim.CLAIMED if result == 1 else BusyClaim.ALREADY_BUSY

    def release_busy(self, courier_id: uuid.UUID) -> None:
        self.redis.srem(self.busy_key, LocationRepository.member(courier_id))
