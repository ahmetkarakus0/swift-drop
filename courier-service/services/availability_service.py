import logging
import uuid

from fastapi import HTTPException, status
from redis.exceptions import RedisError

from repositories.availability_repo import AvailabilityRepository

logger = logging.getLogger(__name__)


class AvailabilityService:
    def __init__(self, availability_repo: AvailabilityRepository):
        self.availability_repo = availability_repo

    def go_online(self, courier_id: uuid.UUID) -> None:
        try:
            self.availability_repo.set_online(courier_id)
        except RedisError:
            logger.exception("Could not mark courier %s online", courier_id)
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE, "Availability updates are temporarily unavailable"
            )

    def go_offline(self, courier_id: uuid.UUID) -> None:
        try:
            self.availability_repo.set_offline(courier_id)
        except RedisError:
            logger.exception("Could not mark courier %s offline", courier_id)
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE, "Availability updates are temporarily unavailable"
            )
