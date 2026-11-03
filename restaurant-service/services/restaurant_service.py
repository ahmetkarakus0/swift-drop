import logging
import uuid

from fastapi import HTTPException, status
from redis.exceptions import RedisError

from models import Restaurant
from repositories.location_repo import RestaurantLocationRepository
from repositories.restaurant_repo import RestaurantRepository
from schemas.restaurant_schema import RestaurantCreate, RestaurantUpdate

logger = logging.getLogger(__name__)


class RestaurantService:
    def __init__(
        self,
        restaurant_repo: RestaurantRepository,
        location_repo: RestaurantLocationRepository,
    ):
        self.restaurant_repo = restaurant_repo
        self.location_repo = location_repo

    def create(self, merchant_id: uuid.UUID, data: RestaurantCreate) -> Restaurant:
        restaurant = self.restaurant_repo.create(Restaurant(**data.model_dump(), merchant_id=merchant_id))
        self._sync_location(restaurant)
        return restaurant

    def get_all(self, merchant_id: uuid.UUID) -> list[Restaurant]:
        return self.restaurant_repo.list_by_merchant(merchant_id)

    def get(self, merchant_id: uuid.UUID, restaurant_id: uuid.UUID) -> Restaurant:
        restaurant = self.restaurant_repo.get_owned(restaurant_id, merchant_id)
        if restaurant is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Restaurant not found")
        return restaurant

    def get_with_menu(self, merchant_id: uuid.UUID, restaurant_id: uuid.UUID) -> Restaurant:
        restaurant = self.restaurant_repo.get_owned_with_menu(restaurant_id, merchant_id)
        if restaurant is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Restaurant not found")
        return restaurant

    def update(
        self, merchant_id: uuid.UUID, restaurant_id: uuid.UUID, data: RestaurantUpdate
    ) -> Restaurant:
        restaurant = self.get(merchant_id, restaurant_id)
        changes = data.changes()
        for field, value in changes.items():
            setattr(restaurant, field, value)
        restaurant = self.restaurant_repo.save(restaurant)
        if "latitude" in changes or "longitude" in changes:
            self._sync_location(restaurant)
        return restaurant

    def delete(self, merchant_id: uuid.UUID, restaurant_id: uuid.UUID) -> None:
        self.restaurant_repo.deactivate(self.get(merchant_id, restaurant_id))
        try:
            self.location_repo.delete(restaurant_id)
        except RedisError:
            logger.exception("Could not remove location of restaurant %s", restaurant_id)

    def _sync_location(self, restaurant: Restaurant) -> None:
        """Best-effort: runs after the database commit and never fails the request."""
        if restaurant.latitude is None or restaurant.longitude is None:
            return
        try:
            self.location_repo.save(restaurant.id, restaurant.latitude, restaurant.longitude)
        except RedisError:
            logger.exception("Could not save location of restaurant %s", restaurant.id)
