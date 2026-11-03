import logging
from typing import Optional

from confluent_kafka import KafkaError, KafkaException, Message, Producer

from schemas.event_schema import CourierSearch, CourierSearchCompletedEvent

logger = logging.getLogger(__name__)


class DispatchEventPublisher:
    """Publishes dispatch events to Kafka, keyed by order id so each order's events stay in order.

    Publishing is best-effort: a failure is logged and never stops event consumption.
    """

    def __init__(self, producer: Producer, topic: str):
        self.producer = producer
        self.topic = topic

    def courier_search_completed(self, search: CourierSearch) -> None:
        event = CourierSearchCompletedEvent(data=search)
        self._publish(str(search.order_id), event.event_type.value, event.model_dump_json())

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
                "Delivery failed for dispatch event (key=%s): %s",
                message.key().decode() if message.key() else None,
                error,
            )
