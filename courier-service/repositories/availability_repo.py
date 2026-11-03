import uuid

from redis import Redis

from repositories.location_repo import LocationRepository


class AvailabilityRepository:
    """Online couriers are kept in a Redis set, using the same members as the location index."""

    def __init__(self, redis: Redis, online_key: str):
        self.redis = redis
        self.online_key = online_key

    def set_online(self, courier_id: uuid.UUID) -> None:
        self.redis.sadd(self.online_key, LocationRepository.member(courier_id))

    def set_offline(self, courier_id: uuid.UUID) -> None:
        self.redis.srem(self.online_key, LocationRepository.member(courier_id))
