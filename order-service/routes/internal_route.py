import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends

from core.dependencies import get_order_service
from models import OrderStatus
from schemas.order_schema import OrderResponse
from services.order_service import OrderService

# Mounted outside /api, so the gateway never forwards these; for service-to-service calls only.
router = APIRouter(prefix="/internal", tags=["internal"])


@router.get("/restaurants/{restaurant_id}/orders", response_model=list[OrderResponse])
def list_restaurant_orders(
    restaurant_id: uuid.UUID,
    order_service: Annotated[OrderService, Depends(get_order_service)],
    status: Optional[OrderStatus] = None,
):
    return order_service.get_all_for_restaurant(restaurant_id, status)


@router.put("/restaurants/{restaurant_id}/orders/{order_id}/accept", response_model=OrderResponse)
def accept_restaurant_order(
    restaurant_id: uuid.UUID,
    order_id: uuid.UUID,
    order_service: Annotated[OrderService, Depends(get_order_service)],
):
    return order_service.accept(restaurant_id, order_id)


@router.put("/restaurants/{restaurant_id}/orders/{order_id}/prepare", response_model=OrderResponse)
def prepare_restaurant_order(
    restaurant_id: uuid.UUID,
    order_id: uuid.UUID,
    order_service: Annotated[OrderService, Depends(get_order_service)],
):
    return order_service.prepare(restaurant_id, order_id)


@router.put(
    "/restaurants/{restaurant_id}/orders/{order_id}/ready-for-pickup",
    response_model=OrderResponse,
)
def mark_restaurant_order_ready_for_pickup(
    restaurant_id: uuid.UUID,
    order_id: uuid.UUID,
    order_service: Annotated[OrderService, Depends(get_order_service)],
):
    return order_service.mark_ready_for_pickup(restaurant_id, order_id)


@router.put("/restaurants/{restaurant_id}/orders/{order_id}/cancel", response_model=OrderResponse)
def cancel_restaurant_order(
    restaurant_id: uuid.UUID,
    order_id: uuid.UUID,
    order_service: Annotated[OrderService, Depends(get_order_service)],
):
    return order_service.cancel(restaurant_id, order_id)
