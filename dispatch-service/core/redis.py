from redis import Redis

from core.config.settings import settings

redis_client = Redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5,
    health_check_interval=30,
)


def get_redis() -> Redis:
    return redis_client
