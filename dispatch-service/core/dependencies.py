from core.config.settings import settings
from core.kafka import create_kafka_consumer, kafka_producer
from core.redis import redis_client
from repositories.availability_repo import CourierAvailabilityRepository
from repositories.location_repo import CourierLocationRepository, RestaurantLocationRepository
from services.courier_search_service import CourierSearchService
from services.dispatch_service import DispatchService
from services.event_publisher import DispatchEventPublisher
from services.order_event_consumer import OrderEventConsumer


def build_dispatch_service() -> DispatchService:
    courier_search_service = CourierSearchService(
        CourierLocationRepository(redis_client, settings.COURIER_LOCATIONS_KEY),
        RestaurantLocationRepository(redis_client, settings.RESTAURANT_LOCATIONS_KEY),
        CourierAvailabilityRepository(
            redis_client, settings.COURIER_ONLINE_KEY, settings.COURIER_BUSY_KEY
        ),
        settings.COURIER_SEARCH_RADII_KM,
    )
    event_publisher = DispatchEventPublisher(kafka_producer, settings.KAFKA_DISPATCH_EVENTS_TOPIC)
    return DispatchService(courier_search_service, event_publisher)


def build_order_event_consumer() -> OrderEventConsumer:
    return OrderEventConsumer(
        create_kafka_consumer(), settings.KAFKA_ORDER_EVENTS_TOPIC, build_dispatch_service()
    )
