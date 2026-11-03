import logging
import uuid

from repositories.availability_repo import CourierAvailabilityRepository
from repositories.location_repo import (
    CourierLocationRepository,
    RestaurantLocationRepository,
    courier_id_from_member,
)
from schemas.dispatch_schema import CourierCandidate, CourierSearchResult

logger = logging.getLogger(__name__)


class CourierSearchService:
    """Finds online, non-busy couriers around a restaurant, widening the radius step by step."""

    def __init__(
        self,
        courier_location_repo: CourierLocationRepository,
        restaurant_location_repo: RestaurantLocationRepository,
        availability_repo: CourierAvailabilityRepository,
        radii_km: list[float],
    ):
        self.courier_location_repo = courier_location_repo
        self.restaurant_location_repo = restaurant_location_repo
        self.availability_repo = availability_repo
        self.radii_km = sorted(radii_km)

    def find_available(self, restaurant_id: uuid.UUID) -> CourierSearchResult:
        """Returns the available couriers in the smallest radius that has any, nearest first."""
        center = self.restaurant_location_repo.get(restaurant_id)
        if center is None:
            logger.warning("Restaurant %s has no stored location; cannot search couriers", restaurant_id)
            return CourierSearchResult()

        for radius_km in self.radii_km:
            nearby = self.courier_location_repo.search(center, radius_km)
            distances = dict(nearby)
            available = self.availability_repo.filter_available([member for member, _ in nearby])
            if available:
                return CourierSearchResult(
                    radius_km=radius_km,
                    candidates=[
                        CourierCandidate(
                            courier_id=courier_id_from_member(member), distance_km=distances[member]
                        )
                        for member in available
                    ],
                )
            logger.info(
                "No available courier within %s km of restaurant %s (%d nearby)",
                radius_km,
                restaurant_id,
                len(nearby),
            )
        return CourierSearchResult()
