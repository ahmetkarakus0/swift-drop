import uuid

from fastapi import HTTPException, status

from models import Restaurant
from repositories.restaurant_repo import RestaurantRepository
from schemas.restaurant_schema import RestaurantCreate, RestaurantUpdate


class RestaurantService:
    def __init__(self, restaurant_repo: RestaurantRepository):
        self.restaurant_repo = restaurant_repo

    def create(self, merchant_id: uuid.UUID, data: RestaurantCreate) -> Restaurant:
        return self.restaurant_repo.create(Restaurant(**data.model_dump(), merchant_id=merchant_id))

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
        for field, value in data.changes().items():
            setattr(restaurant, field, value)
        return self.restaurant_repo.save(restaurant)

    def delete(self, merchant_id: uuid.UUID, restaurant_id: uuid.UUID) -> None:
        self.restaurant_repo.deactivate(self.get(merchant_id, restaurant_id))
