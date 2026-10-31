import logging
import uuid
from typing import Optional

import httpx
from fastapi import HTTPException, status
from pydantic import TypeAdapter, ValidationError

from repositories.restaurant_repo import RestaurantRepository
from schemas.order_schema import OrderResponse, OrderStatus

logger = logging.getLogger(__name__)

RESTAURANT_ORDERS_PATH = "/internal/restaurants/{restaurant_id}/orders"

_orders_adapter = TypeAdapter(list[OrderResponse])


class OrderService:
    """Reads a restaurant's orders from order-service."""

    def __init__(self, client: httpx.Client, restaurant_repo: RestaurantRepository):
        self.client = client
        self.restaurant_repo = restaurant_repo

    def get_all(
        self,
        merchant_id: uuid.UUID,
        restaurant_id: uuid.UUID,
        order_status: Optional[OrderStatus] = None,
    ) -> list[OrderResponse]:
        if self.restaurant_repo.get_owned(restaurant_id, merchant_id) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Restaurant not found")

        path = RESTAURANT_ORDERS_PATH.format(restaurant_id=restaurant_id)
        params = {"status": order_status.value} if order_status is not None else None
        try:
            response = self.client.get(path, params=params)
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
