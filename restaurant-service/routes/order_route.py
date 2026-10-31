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
