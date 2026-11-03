import enum
import uuid
from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field

from models import OrderStatus
from schemas.order_schema import OrderResponse


class OrderEventType(str, enum.Enum):
    ORDER_CREATED = "order.created"
    ORDER_STATUS_UPDATED = "order.status_updated"
    ORDER_COURIER_ASSIGNED = "order.courier_assigned"


class OrderStatusChange(BaseModel):
    order_id: uuid.UUID
    user_id: uuid.UUID
    restaurant_id: uuid.UUID
    courier_id: Optional[uuid.UUID]
    previous_status: OrderStatus
    status: OrderStatus
    updated_at: datetime


class CourierAssignment(BaseModel):
    order_id: uuid.UUID
    user_id: uuid.UUID
    restaurant_id: uuid.UUID
    courier_id: uuid.UUID
    status: OrderStatus
    updated_at: datetime


class _EventEnvelope(BaseModel):
    event_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class OrderCreatedEvent(_EventEnvelope):
    event_type: Literal[OrderEventType.ORDER_CREATED] = OrderEventType.ORDER_CREATED
    data: OrderResponse


class OrderStatusUpdatedEvent(_EventEnvelope):
    event_type: Literal[OrderEventType.ORDER_STATUS_UPDATED] = OrderEventType.ORDER_STATUS_UPDATED
    data: OrderStatusChange


class OrderCourierAssignedEvent(_EventEnvelope):
    event_type: Literal[OrderEventType.ORDER_COURIER_ASSIGNED] = (
        OrderEventType.ORDER_COURIER_ASSIGNED
    )
    data: CourierAssignment
