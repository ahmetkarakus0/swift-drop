import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends

from core.dependencies import get_current_merchant_id, get_order_service
from schemas.order_schema import OrderResponse, OrderStatus
from services.order_service import OrderService

router = APIRouter(tags=["orders"])


@router.get("/restaurants/{restaurant_id}/orders", response_model=list[OrderResponse])
def list_orders(
    restaurant_id: uuid.UUID,
    merchant_id: Annotated[uuid.UUID, Depends(get_current_merchant_id)],
    order_service: Annotated[OrderService, Depends(get_order_service)],
    status: Optional[OrderStatus] = None,
):
    return order_service.get_all(merchant_id, restaurant_id, status)


@router.put("/restaurants/{restaurant_id}/orders/{order_id}/accept", response_model=OrderResponse)
def accept_order(
    restaurant_id: uuid.UUID,
    order_id: uuid.UUID,
    merchant_id: Annotated[uuid.UUID, Depends(get_current_merchant_id)],
    order_service: Annotated[OrderService, Depends(get_order_service)],
):
    return order_service.accept(merchant_id, restaurant_id, order_id)


@router.put("/restaurants/{restaurant_id}/orders/{order_id}/prepare", response_model=OrderResponse)
def prepare_order(
    restaurant_id: uuid.UUID,
    order_id: uuid.UUID,
    merchant_id: Annotated[uuid.UUID, Depends(get_current_merchant_id)],
    order_service: Annotated[OrderService, Depends(get_order_service)],
):
    return order_service.prepare(merchant_id, restaurant_id, order_id)


@router.put(
    "/restaurants/{restaurant_id}/orders/{order_id}/ready-for-pickup",
    response_model=OrderResponse,
)
def mark_order_ready_for_pickup(
    restaurant_id: uuid.UUID,
    order_id: uuid.UUID,
    merchant_id: Annotated[uuid.UUID, Depends(get_current_merchant_id)],
    order_service: Annotated[OrderService, Depends(get_order_service)],
):
    return order_service.mark_ready_for_pickup(merchant_id, restaurant_id, order_id)


@router.put("/restaurants/{restaurant_id}/orders/{order_id}/cancel", response_model=OrderResponse)
def cancel_order(
    restaurant_id: uuid.UUID,
    order_id: uuid.UUID,
    merchant_id: Annotated[uuid.UUID, Depends(get_current_merchant_id)],
    order_service: Annotated[OrderService, Depends(get_order_service)],
):
    return order_service.cancel(merchant_id, restaurant_id, order_id)
