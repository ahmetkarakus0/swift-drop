import logging
import time
from collections.abc import Callable

from redis import Redis
from sqlalchemy import Engine, text

from schemas.health_schema import HealthResponse, ServiceHealth

logger = logging.getLogger(__name__)


class HealthService:
    def __init__(self, engine: Engine, redis: Redis):
        self.engine = engine
        self.redis = redis

    def check(self) -> HealthResponse:
        services = {
            "postgresql": self._run("postgresql", self._check_postgresql),
            "redis": self._run("redis", self._check_redis),
        }
        healthy = all(s.status == "up" for s in services.values())
        return HealthResponse(status="up" if healthy else "down", services=services)

    def _check_postgresql(self) -> None:
        with self.engine.connect() as connection:
            connection.execute(text("SELECT 1"))

    def _check_redis(self) -> None:
        self.redis.ping()

    @staticmethod
    def _run(name: str, check: Callable[[], None]) -> ServiceHealth:
        started = time.perf_counter()
        try:
            check()
        except Exception:
            # Details stay in the logs; the response must not leak connection info.
            logger.exception("%s health check failed", name)
            return ServiceHealth(status="down")
        return ServiceHealth(
            status="up", latency_ms=round((time.perf_counter() - started) * 1000, 2)
        )
