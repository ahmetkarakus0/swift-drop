import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from core.config.settings import settings
from core.dependencies import (
    get_availability_service,
    get_current_courier_id,
    get_location_service,
    get_nearby_order_service,
    get_order_selection_service,
    get_order_service,
)
from schemas.location_schema import CourierLocationUpdate
from schemas.order_schema import CourierOrderResponse, NearbyOrderResponse
from services.availability_service import AvailabilityService
from services.location_service import LocationService
from services.nearby_order_service import NearbyOrderService
from services.order_selection_service import OrderSelectionService
from services.order_service import OrderService

router = APIRouter(prefix="/couriers", tags=["couriers"])


@router.put("/location", status_code=status.HTTP_204_NO_CONTENT)
def update_location(
    data: CourierLocationUpdate,
    courier_id: Annotated[uuid.UUID, Depends(get_current_courier_id)],
    location_service: Annotated[LocationService, Depends(get_location_service)],
):
    location_service.update_location(courier_id, data)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/online", status_code=status.HTTP_204_NO_CONTENT)
def go_online(
    courier_id: Annotated[uuid.UUID, Depends(get_current_courier_id)],
    availability_service: Annotated[AvailabilityService, Depends(get_availability_service)],
):
    availability_service.go_online(courier_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/offline", status_code=status.HTTP_204_NO_CONTENT)
def go_offline(
    courier_id: Annotated[uuid.UUID, Depends(get_current_courier_id)],
    availability_service: Annotated[AvailabilityService, Depends(get_availability_service)],
):
    availability_service.go_offline(courier_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/orders/nearby", response_model=list[NearbyOrderResponse])
def list_nearby_orders(
    courier_id: Annotated[uuid.UUID, Depends(get_current_courier_id)],
    nearby_order_service: Annotated[NearbyOrderService, Depends(get_nearby_order_service)],
    radius_km: Annotated[
        float, Query(gt=0, le=settings.NEARBY_ORDERS_MAX_RADIUS_KM)
    ] = settings.NEARBY_ORDERS_DEFAULT_RADIUS_KM,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
):
    return nearby_order_service.find_nearest(courier_id, radius_km, limit)


@router.put("/orders/{order_id}/select", response_model=CourierOrderResponse)
def select_order(
    order_id: uuid.UUID,
    courier_id: Annotated[uuid.UUID, Depends(get_current_courier_id)],
    order_selection_service: Annotated[OrderSelectionService, Depends(get_order_selection_service)],
):
    return order_selection_service.select(courier_id, order_id)


@router.put("/orders/{order_id}/on-the-way", response_model=CourierOrderResponse)
def mark_order_on_the_way(
    order_id: uuid.UUID,
    courier_id: Annotated[uuid.UUID, Depends(get_current_courier_id)],
    order_service: Annotated[OrderService, Depends(get_order_service)],
):
    return order_service.mark_on_the_way(courier_id, order_id)
