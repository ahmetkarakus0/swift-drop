import logging
from typing import Optional

from confluent_kafka import KafkaError, KafkaException, Message, Producer

from models import Order, OrderStatus
from schemas.event_schema import (
    CourierAssignment,
    OrderCourierAssignedEvent,
    OrderCreatedEvent,
    OrderStatusChange,
    OrderStatusUpdatedEvent,
)
from schemas.order_schema import OrderResponse

logger = logging.getLogger(__name__)


class OrderEventPublisher:
    """Publishes order events to Kafka, keyed by order id so each order's events stay in order.

    Publishing is best-effort: it runs after the database commit and never fails the request.
    """

    def __init__(self, producer: Producer, topic: str):
        self.producer = producer
        self.topic = topic

    def order_created(self, order: Order) -> None:
        event = OrderCreatedEvent(data=OrderResponse.model_validate(order))
        self._publish(str(order.id), event.event_type.value, event.model_dump_json())

    def order_status_updated(self, order: Order, previous_status: OrderStatus) -> None:
        event = OrderStatusUpdatedEvent(
            data=OrderStatusChange(
                order_id=order.id,
                user_id=order.user_id,
                restaurant_id=order.restaurant_id,
                courier_id=order.courier_id,
                previous_status=previous_status,
                status=order.status,
                updated_at=order.updated_at,
            )
        )
        self._publish(str(order.id), event.event_type.value, event.model_dump_json())

    def courier_assigned(self, order: Order) -> None:
        event = OrderCourierAssignedEvent(
            data=CourierAssignment(
                order_id=order.id,
                user_id=order.user_id,
                restaurant_id=order.restaurant_id,
                courier_id=order.courier_id,
                status=order.status,
                updated_at=order.updated_at,
            )
        )
        self._publish(str(order.id), event.event_type.value, event.model_dump_json())

    def _publish(self, key: str, event_type: str, payload: str) -> None:
        try:
            self.producer.produce(
                self.topic,
                key=key,
                value=payload,
                headers={"event_type": event_type},
                on_delivery=self._on_delivery,
            )
            self.producer.poll(0)
        except (BufferError, KafkaException):
            logger.exception("Could not publish %s for order %s", event_type, key)

    @staticmethod
    def _on_delivery(error: Optional[KafkaError], message: Message) -> None:
        if error is not None:
            logger.error(
                "Delivery failed for order event (key=%s): %s",
                message.key().decode() if message.key() else None,
                error,
            )
