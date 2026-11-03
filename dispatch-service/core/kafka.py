from confluent_kafka import Consumer, Producer

from core.config.settings import settings

kafka_producer = Producer(
    {
        "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
        "client.id": "dispatch-service",
        "enable.idempotence": True,
        "acks": "all",
    }
)


def get_kafka_producer() -> Producer:
    return kafka_producer


def create_kafka_consumer() -> Consumer:
    """Offsets are stored only after a message is handled, so a crash replays it (at-least-once)."""
    return Consumer(
        {
            "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
            "client.id": "dispatch-service",
            "group.id": settings.KAFKA_CONSUMER_GROUP_ID,
            "auto.offset.reset": settings.KAFKA_AUTO_OFFSET_RESET,
            "enable.auto.commit": True,
            "enable.auto.offset.store": False,
        }
    )
