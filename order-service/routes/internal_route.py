import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends

from core.dependencies import get_order_service
from models import OrderStatus
from schemas.order_schema import CourierAssign, OrderResponse, ReadyForPickupSearch
from services.order_service import OrderService

# Mounted outside /api, so the gateway never forwards these; for service-to-service calls only.
router = APIRouter(prefix="/internal", tags=["internal"])


# POST because the restaurant list can be too long for a query string.
@router.post("/orders/ready-for-pickup/search", response_model=list[OrderResponse])
def search_unassigned_ready_for_pickup_orders(
    data: ReadyForPickupSearch,
    order_service: Annotated[OrderService, Depends(get_order_service)],
):
    return order_service.get_unassigned_ready_for_pickup(data.restaurant_ids)


@router.put("/orders/{order_id}/courier", response_model=OrderResponse)
def assign_order_courier(
    order_id: uuid.UUID,
    data: CourierAssign,
    order_service: Annotated[OrderService, Depends(get_order_service)],
):
    return order_service.assign_courier(order_id, data.courier_id)


@router.put("/couriers/{courier_id}/orders/{order_id}/on-the-way", response_model=OrderResponse)
def mark_courier_order_on_the_way(
    courier_id: uuid.UUID,
    order_id: uuid.UUID,
    order_service: Annotated[OrderService, Depends(get_order_service)],
):
    return order_service.mark_on_the_way(courier_id, order_id)


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
