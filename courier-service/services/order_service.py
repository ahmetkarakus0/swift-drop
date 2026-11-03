import logging
import uuid

import httpx
from fastapi import HTTPException, status
from pydantic import TypeAdapter, ValidationError

from schemas.order_schema import ReadyOrder

logger = logging.getLogger(__name__)

READY_FOR_PICKUP_SEARCH_PATH = "/internal/orders/ready-for-pickup/search"

_orders_adapter = TypeAdapter(list[ReadyOrder])


class OrderService:
    """Reads orders from order-service."""

    def __init__(self, client: httpx.Client):
        self.client = client

    def get_unassigned_ready_for_pickup(self, restaurant_ids: list[uuid.UUID]) -> list[ReadyOrder]:
        """Returns orders of the given restaurants waiting for a courier, oldest ready first."""
        path = READY_FOR_PICKUP_SEARCH_PATH
        try:
            response = self.client.post(
                path, json={"restaurant_ids": [str(restaurant_id) for restaurant_id in restaurant_ids]}
            )
        except httpx.HTTPError:
            logger.exception("Could not reach order-service")
            raise self._orders_unavailable_error()

        if response.is_error:
            logger.error("order-service returned %s for %s", response.status_code, path)
            raise self._orders_unavailable_error()

        try:
            return _orders_adapter.validate_json(response.content)
        except ValidationError:
            logger.exception("Unexpected response from order-service %s", path)
            raise self._orders_unavailable_error()

    @staticmethod
    def _orders_unavailable_error() -> HTTPException:
        return HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "Orders are temporarily unavailable"
        )
