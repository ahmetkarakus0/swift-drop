import uuid
from datetime import datetime
from decimal import Decimal

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
