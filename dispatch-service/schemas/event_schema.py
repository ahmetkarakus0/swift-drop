import enum
import uuid
from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field

from schemas.dispatch_schema import CourierCandidate


class DispatchEventType(str, enum.Enum):
    COURIER_SEARCH_COMPLETED = "dispatch.courier_search_completed"


class OrderEventType(str, enum.Enum):
    ORDER_CREATED = "order.created"
    ORDER_STATUS_UPDATED = "order.status_updated"


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY_FOR_PICKUP = "ready_for_pickup"
    ON_THE_WAY = "on_the_way"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class OrderStatusChange(BaseModel):
    order_id: uuid.UUID
    user_id: uuid.UUID
    restaurant_id: uuid.UUID
    courier_id: Optional[uuid.UUID]
    previous_status: OrderStatus
    status: OrderStatus
    updated_at: datetime


class OrderStatusUpdatedEvent(BaseModel):
    """Published by order-service to the order events topic."""

    event_id: uuid.UUID
    occurred_at: datetime
    event_type: Literal[OrderEventType.ORDER_STATUS_UPDATED]
    data: OrderStatusChange


class CourierSearch(BaseModel):
    order_id: uuid.UUID
    restaurant_id: uuid.UUID
    radius_km: Optional[float]
    candidates: list[CourierCandidate]


class CourierSearchCompletedEvent(BaseModel):
    """Published by dispatch-service to the dispatch events topic."""

    event_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: Literal[DispatchEventType.COURIER_SEARCH_COMPLETED] = (
        DispatchEventType.COURIER_SEARCH_COMPLETED
    )
    data: CourierSearch
