import json
import time
import uuid
from typing import Any

from confluent_kafka import Consumer, KafkaException, TopicPartition


class OrderEvents:
    """Reads order-service's Kafka topic starting from where it ends when the helper is created,
    so a case only sees the events it caused."""

    def __init__(self, bootstrap_servers: str, topic: str, timeout_seconds: float):
        self.topic = topic
        self.timeout_seconds = timeout_seconds
        self.consumer = Consumer(
            {
                "bootstrap.servers": bootstrap_servers,
                "group.id": f"e2e-{uuid.uuid4().hex}",
                "enable.auto.commit": False,
            }
        )
        self.consumer.assign(self._end_offsets())
        self._seen: list[dict[str, Any]] = []

    def _end_offsets(self) -> list[TopicPartition]:
        metadata = self.consumer.list_topics(self.topic, timeout=self.timeout_seconds)
        topic = metadata.topics.get(self.topic)
        if topic is None or topic.error is not None or not topic.partitions:
            raise KafkaException(f"Topic {self.topic} is not available")
        positions = []
        for partition in topic.partitions:
            _, high = self.consumer.get_watermark_offsets(
                TopicPartition(self.topic, partition), timeout=self.timeout_seconds
            )
            positions.append(TopicPartition(self.topic, partition, high))
        return positions

    def for_order(self, order_id: str, count: int) -> list[dict[str, Any]]:
        """Waits until `count` events keyed by `order_id` have arrived and returns them in publish order.
        Each event is the JSON payload plus the `event_type` header under `header_event_type`."""
        deadline = time.monotonic() + self.timeout_seconds
        while len(self._matching(order_id)) < count and time.monotonic() < deadline:
            message = self.consumer.poll(0.5)
            if message is None:
                continue
            if message.error() is not None:
                raise KafkaException(message.error())
            headers = dict(message.headers() or [])
            event = json.loads(message.value())
            event["_key"] = message.key().decode() if message.key() else None
            event["header_event_type"] = headers.get("event_type", b"").decode()
            self._seen.append(event)
        matching = self._matching(order_id)
        assert len(matching) >= count, (
            f"Expected {count} events for order {order_id} on {self.topic}, got {len(matching)}: {matching}"
        )
        return matching

    def _matching(self, order_id: str) -> list[dict[str, Any]]:
        return [event for event in self._seen if event["_key"] == order_id]

    def close(self) -> None:
        self.consumer.close()
