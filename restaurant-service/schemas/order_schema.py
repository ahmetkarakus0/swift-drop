import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY_FOR_PICKUP = "ready_for_pickup"
    ON_THE_WAY = "on_the_way"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class OrderItemResponse(BaseModel):
    id: uuid.UUID
    item_id: int
    item_name: str
    quantity: int
    price: Decimal


class OrderResponse(BaseModel):
    """order-service's GET /internal/restaurants/{restaurant_id}/orders response item."""

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
