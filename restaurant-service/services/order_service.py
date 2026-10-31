import logging
import uuid
from typing import Any, Optional

import httpx
from fastapi import HTTPException, status
from pydantic import TypeAdapter, ValidationError

from repositories.restaurant_repo import RestaurantRepository
from schemas.order_schema import OrderResponse, OrderStatus

logger = logging.getLogger(__name__)

RESTAURANT_ORDERS_PATH = "/internal/restaurants/{restaurant_id}/orders"
ACCEPT_ORDER_PATH = "/internal/restaurants/{restaurant_id}/orders/{order_id}/accept"

_orders_adapter = TypeAdapter(list[OrderResponse])


class OrderService:
    """Reads and updates a restaurant's orders in order-service."""

    def __init__(self, client: httpx.Client, restaurant_repo: RestaurantRepository):
        self.client = client
        self.restaurant_repo = restaurant_repo

    def get_all(
        self,
        merchant_id: uuid.UUID,
        restaurant_id: uuid.UUID,
        order_status: Optional[OrderStatus] = None,
    ) -> list[OrderResponse]:
        self._ensure_restaurant_owned(merchant_id, restaurant_id)
        path = RESTAURANT_ORDERS_PATH.format(restaurant_id=restaurant_id)
        params = {"status": order_status.value} if order_status is not None else None
        response = self._request("GET", path, params=params)
        return self._parse(response, path, _orders_adapter.validate_json)

    def accept(
        self, merchant_id: uuid.UUID, restaurant_id: uuid.UUID, order_id: uuid.UUID
    ) -> OrderResponse:
        self._ensure_restaurant_owned(merchant_id, restaurant_id)
        path = ACCEPT_ORDER_PATH.format(restaurant_id=restaurant_id, order_id=order_id)
        response = self._request("PUT", path)
        return self._parse(response, path, OrderResponse.model_validate_json)

    def _ensure_restaurant_owned(self, merchant_id: uuid.UUID, restaurant_id: uuid.UUID) -> None:
        if self.restaurant_repo.get_owned(restaurant_id, merchant_id) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Restaurant not found")

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        try:
            response = self.client.request(method, path, **kwargs)
        except httpx.HTTPError:
            logger.exception("Could not reach order-service")
            raise self._orders_unavailable_error()

        if response.status_code in (status.HTTP_404_NOT_FOUND, status.HTTP_409_CONFLICT):
            raise HTTPException(response.status_code, self._detail(response, "Order not found"))
        if response.is_error:
            logger.error("order-service returned %s for %s %s", response.status_code, method, path)
            raise self._orders_unavailable_error()
        return response

    def _parse(self, response: httpx.Response, path: str, validate: Any) -> Any:
        try:
            return validate(response.content)
        except ValidationError:
            logger.exception("Unexpected response from order-service %s", path)
            raise self._orders_unavailable_error()

    @staticmethod
    def _detail(response: httpx.Response, fallback: str) -> str:
        try:
            detail = response.json().get("detail")
        except (ValueError, AttributeError):
            return fallback
        return detail if isinstance(detail, str) else fallback

    @staticmethod
    def _orders_unavailable_error() -> HTTPException:
        return HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "Orders are temporarily unavailable"
        )
