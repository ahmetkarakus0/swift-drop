import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from core.dependencies import get_current_customer_user_id, get_order_service
from schemas.order_schema import OrderCreate, OrderResponse
from services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def place_order(
    data: OrderCreate,
    user_id: Annotated[uuid.UUID, Depends(get_current_customer_user_id)],
    order_service: Annotated[OrderService, Depends(get_order_service)],
):
    return order_service.place(user_id, data)
