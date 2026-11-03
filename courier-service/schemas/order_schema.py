import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class OrderItemResponse(BaseModel):
    item_name: str
    quantity: int


class ReadyOrder(BaseModel):
    """order-service's POST /internal/orders/ready-for-pickup/search response item."""

    id: uuid.UUID
    restaurant_id: uuid.UUID
    total_price: Decimal
    delivery_address: str
    items: list[OrderItemResponse]
    created_at: datetime
    updated_at: datetime


class NearbyOrderResponse(BaseModel):
    id: uuid.UUID
    restaurant_id: uuid.UUID
    distance_km: float
    total_price: Decimal
    delivery_address: str
    items: list[OrderItemResponse]
    created_at: datetime
    ready_at: datetime


class CourierOrderResponse(BaseModel):
    """order-service's response for a courier's order (assign, on the way)."""

    id: uuid.UUID
    restaurant_id: uuid.UUID
    courier_id: Optional[uuid.UUID]
    status: str
    total_price: Decimal
    delivery_address: str
    items: list[OrderItemResponse]
    created_at: datetime
    updated_at: datetime
