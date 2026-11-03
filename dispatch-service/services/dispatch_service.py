import logging
from typing import Optional

from schemas.dispatch_schema import CourierSearchResult
from schemas.event_schema import CourierSearch, OrderStatus, OrderStatusUpdatedEvent
from services.courier_search_service import CourierSearchService
from services.event_publisher import DispatchEventPublisher

logger = logging.getLogger(__name__)


class DispatchService:
    def __init__(
        self, courier_search_service: CourierSearchService, event_publisher: DispatchEventPublisher
    ):
        self.courier_search_service = courier_search_service
        self.event_publisher = event_publisher

    def handle_order_status_updated(self, event: OrderStatusUpdatedEvent) -> Optional[CourierSearchResult]:
        """Searches couriers when an order becomes ready for pickup; returns None for other changes."""
        change = event.data
        if (
            change.status != OrderStatus.READY_FOR_PICKUP
            or change.previous_status == OrderStatus.READY_FOR_PICKUP
        ):
            return None

        result = self.courier_search_service.find_available(change.restaurant_id)
        if result.candidates:
            logger.info(
                "Found %d available courier(s) for order %s within %s km; nearest is %s at %.2f km",
                len(result.candidates),
                change.order_id,
                result.radius_km,
                result.candidates[0].courier_id,
                result.candidates[0].distance_km,
            )
        else:
            logger.warning("No available courier found for order %s", change.order_id)

        self.event_publisher.courier_search_completed(
            CourierSearch(
                order_id=change.order_id,
                restaurant_id=change.restaurant_id,
                radius_km=result.radius_km,
                candidates=result.candidates,
            )
        )
        return result
