import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict

from models import OrderStatus
from schemas.common import DeliveryAddress


class OrderCreate(BaseModel):
    basket_id: uuid.UUID
    delivery_address: DeliveryAddress


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    item_id: int
    item_name: str
    quantity: int
    price: Decimal


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    restaurant_id: uuid.UUID
    courier_id: Optional[uuid.UUID]
    status: OrderStatus
    total_price: Decimal
    delivery_address: str
    items: list[OrderItemResponse]
    created_at: datetime
    updated_at: datetime
