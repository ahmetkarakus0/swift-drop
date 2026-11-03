import logging
import threading
from typing import Optional

from confluent_kafka import Consumer, KafkaException, Message
from pydantic import ValidationError
from redis.exceptions import RedisError

from schemas.event_schema import OrderEventType, OrderStatusUpdatedEvent
from services.dispatch_service import DispatchService

logger = logging.getLogger(__name__)

POLL_TIMEOUT_SECONDS = 1.0


class OrderEventConsumer:
    """Consumes order events on a background thread and hands status updates to dispatch.

    A message whose handling fails is logged and skipped, so one bad event never blocks the partition.
    """

    def __init__(self, consumer: Consumer, topic: str, dispatch_service: DispatchService):
        self.consumer = consumer
        self.topic = topic
        self.dispatch_service = dispatch_service
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="order-event-consumer", daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self, timeout: float) -> None:
        self._stop.set()
        self._thread.join(timeout)
        if self._thread.is_alive():
            logger.warning("Order event consumer did not stop within %s seconds", timeout)

    def _run(self) -> None:
        try:
            self.consumer.subscribe([self.topic])
            while not self._stop.is_set():
                message = self.consumer.poll(POLL_TIMEOUT_SECONDS)
                if message is None:
                    continue
                if message.error():
                    logger.error("Kafka consumer error: %s", message.error())
                    continue
                self._handle(message)
                self.consumer.store_offsets(message=message)
        except KafkaException:
            logger.exception("Order event consumer stopped because of a Kafka error")
        finally:
            self.consumer.close()

    def _handle(self, message: Message) -> None:
        if self._event_type(message) != OrderEventType.ORDER_STATUS_UPDATED.value:
            return
        try:
            event = OrderStatusUpdatedEvent.model_validate_json(message.value())
        except ValidationError:
            logger.exception("Skipping malformed order event at offset %s", message.offset())
            return
        try:
            self.dispatch_service.handle_order_status_updated(event)
        except RedisError:
            logger.exception("Could not search couriers for order %s", event.data.order_id)

    @staticmethod
    def _event_type(message: Message) -> Optional[str]:
        for key, value in message.headers() or []:
            if key == "event_type" and value is not None:
                return value.decode()
        return None
