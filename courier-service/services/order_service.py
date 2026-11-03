import logging
import uuid
from typing import Any

import httpx
from fastapi import HTTPException, status
from pydantic import TypeAdapter, ValidationError

from schemas.order_schema import CourierOrderResponse, ReadyOrder

logger = logging.getLogger(__name__)

READY_FOR_PICKUP_SEARCH_PATH = "/internal/orders/ready-for-pickup/search"
ORDER_COURIER_PATH = "/internal/orders/{order_id}/courier"
COURIER_ORDER_ON_THE_WAY_PATH = "/internal/couriers/{courier_id}/orders/{order_id}/on-the-way"

_orders_adapter = TypeAdapter(list[ReadyOrder])


class OrderService:
    """Reads and assigns orders in order-service."""

    def __init__(self, client: httpx.Client):
        self.client = client

    def get_unassigned_ready_for_pickup(self, restaurant_ids: list[uuid.UUID]) -> list[ReadyOrder]:
        """Returns orders of the given restaurants waiting for a courier, oldest ready first."""
        path = READY_FOR_PICKUP_SEARCH_PATH
        response = self._request(
            "POST",
            path,
            json={"restaurant_ids": [str(restaurant_id) for restaurant_id in restaurant_ids]},
        )
        return self._parse(response, path, _orders_adapter.validate_json)

    def assign_courier(self, order_id: uuid.UUID, courier_id: uuid.UUID) -> CourierOrderResponse:
        path = ORDER_COURIER_PATH.format(order_id=order_id)
        response = self._request("PUT", path, json={"courier_id": str(courier_id)})
        return self._parse(response, path, CourierOrderResponse.model_validate_json)

    def mark_on_the_way(self, courier_id: uuid.UUID, order_id: uuid.UUID) -> CourierOrderResponse:
        path = COURIER_ORDER_ON_THE_WAY_PATH.format(courier_id=courier_id, order_id=order_id)
        response = self._request("PUT", path)
        return self._parse(response, path, CourierOrderResponse.model_validate_json)

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
