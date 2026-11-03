from redis import Redis


class CourierAvailabilityRepository:
    """Online and busy couriers are Redis sets whose members match the courier location index."""

    def __init__(self, redis: Redis, online_key: str, busy_key: str):
        self.redis = redis
        self.online_key = online_key
        self.busy_key = busy_key

    def filter_available(self, members: list[str]) -> list[str]:
        """Keeps the members that are online and not busy, preserving their order."""
        if not members:
            return []
        pipeline = self.redis.pipeline(transaction=False)
        pipeline.smismember(self.online_key, members)
        pipeline.smismember(self.busy_key, members)
        online, busy = pipeline.execute()
        return [
            member
            for member, is_online, is_busy in zip(members, online, busy)
            if is_online and not is_busy
        ]
