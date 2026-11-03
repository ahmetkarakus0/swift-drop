import logging
import uuid

from fastapi import HTTPException, status
from redis.exceptions import RedisError

from repositories.location_repo import LocationRepository
from repositories.restaurant_location_repo import RestaurantLocationRepository
from schemas.order_schema import NearbyOrderResponse
from services.order_service import OrderService

logger = logging.getLogger(__name__)

# order-service rejects larger restaurant lists.
MAX_RESTAURANTS_PER_SEARCH = 1000


class NearbyOrderService:
    def __init__(
        self,
        location_repo: LocationRepository,
        restaurant_location_repo: RestaurantLocationRepository,
        order_service: OrderService,
    ):
        self.location_repo = location_repo
        self.restaurant_location_repo = restaurant_location_repo
        self.order_service = order_service

    def find_nearest(
        self, courier_id: uuid.UUID, radius_km: float, limit: int
    ) -> list[NearbyOrderResponse]:
        """Returns orders waiting for a courier at restaurants within the radius of the courier.

        Nearest restaurant first; orders of the same restaurant oldest ready first.
        """
        try:
            position = self.location_repo.get(courier_id)
            if position is None:
                raise HTTPException(
                    status.HTTP_409_CONFLICT, "Send your location before looking for orders"
                )
            restaurants = self.restaurant_location_repo.search(position, radius_km)
        except RedisError:
            logger.exception("Could not search restaurants near courier %s", courier_id)
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE, "Nearby orders are temporarily unavailable"
            )

        restaurants = restaurants[:MAX_RESTAURANTS_PER_SEARCH]
        if not restaurants:
            return []

        distances = dict(restaurants)
        orders = self.order_service.get_unassigned_ready_for_pickup(list(distances))
        orders.sort(key=lambda order: distances[order.restaurant_id])
        return [
            NearbyOrderResponse(
                id=order.id,
                restaurant_id=order.restaurant_id,
                distance_km=round(distances[order.restaurant_id], 3),
                total_price=order.total_price,
                delivery_address=order.delivery_address,
                items=order.items,
                created_at=order.created_at,
                ready_at=order.updated_at,
            )
            for order in orders[:limit]
        ]
