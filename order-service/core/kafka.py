from confluent_kafka import Producer

from core.config.settings import settings

kafka_producer = Producer(
    {
        "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
        "client.id": "order-service",
        "enable.idempotence": True,
        "acks": "all",
    }
)


def get_kafka_producer() -> Producer:
    return kafka_producer
