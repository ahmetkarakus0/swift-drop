import logging
import uuid

from fastapi import HTTPException, status
from redis.exceptions import RedisError

from repositories.availability_repo import AvailabilityRepository, BusyClaim
from schemas.order_schema import CourierOrderResponse
from services.order_service import OrderService

logger = logging.getLogger(__name__)


class OrderSelectionService:
    def __init__(self, availability_repo: AvailabilityRepository, order_service: OrderService):
        self.availability_repo = availability_repo
        self.order_service = order_service

    def select(self, courier_id: uuid.UUID, order_id: uuid.UUID) -> CourierOrderResponse:
        """Assigns the order to an online courier and marks them busy.

        The courier is marked busy first, so a courier can never hold two orders; if the assignment
        fails, they are released again.
        """
        try:
            claim = self.availability_repo.claim_busy(courier_id)
        except RedisError:
            logger.exception("Could not mark courier %s busy", courier_id)
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE, "Order selection is temporarily unavailable"
            )
        if claim == BusyClaim.OFFLINE:
            raise HTTPException(status.HTTP_409_CONFLICT, "Go online before selecting an order")
        if claim == BusyClaim.ALREADY_BUSY:
            raise HTTPException(status.HTTP_409_CONFLICT, "You already have an order")

        try:
            return self.order_service.assign_courier(order_id, courier_id)
        except HTTPException:
            self._release(courier_id)
            raise

    def _release(self, courier_id: uuid.UUID) -> None:
        try:
            self.availability_repo.release_busy(courier_id)
        except RedisError:
            logger.exception("Could not release courier %s after a failed selection", courier_id)
