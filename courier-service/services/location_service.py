import logging
import uuid

from fastapi import HTTPException, status
from redis.exceptions import RedisError

from repositories.location_repo import LocationRepository
from schemas.location_schema import CourierLocationUpdate

logger = logging.getLogger(__name__)


class LocationService:
    def __init__(self, location_repo: LocationRepository):
        self.location_repo = location_repo

    def update_location(self, courier_id: uuid.UUID, data: CourierLocationUpdate) -> None:
        try:
            self.location_repo.save(courier_id, data.latitude, data.longitude)
        except RedisError:
            logger.exception("Could not save location of courier %s", courier_id)
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE, "Location updates are temporarily unavailable"
            )
