import uuid

from fastapi import HTTPException, status

from models import Category
from repositories.category_repo import CategoryRepository
from repositories.restaurant_repo import RestaurantRepository
from schemas.category_schema import CategoryCreate, CategoryUpdate


class CategoryService:
    def __init__(self, restaurant_repo: RestaurantRepository, category_repo: CategoryRepository):
        self.restaurant_repo = restaurant_repo
        self.category_repo = category_repo

    def create(
        self, merchant_id: uuid.UUID, restaurant_id: uuid.UUID, data: CategoryCreate
    ) -> Category:
        self._ensure_restaurant_owned(merchant_id, restaurant_id)
        return self.category_repo.create(Category(**data.model_dump(), restaurant_id=restaurant_id))

    def get_all(self, merchant_id: uuid.UUID, restaurant_id: uuid.UUID) -> list[Category]:
        self._ensure_restaurant_owned(merchant_id, restaurant_id)
        return self.category_repo.list_by_restaurant(restaurant_id)

    def get(self, merchant_id: uuid.UUID, category_id: int) -> Category:
        category = self.category_repo.get_owned(category_id, merchant_id)
        if category is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Category not found")
        return category

    def update(self, merchant_id: uuid.UUID, category_id: int, data: CategoryUpdate) -> Category:
        category = self.get(merchant_id, category_id)
        for field, value in data.changes().items():
            setattr(category, field, value)
        return self.category_repo.save(category)

    def delete(self, merchant_id: uuid.UUID, category_id: int) -> None:
        self.category_repo.delete(self.get(merchant_id, category_id))

    def _ensure_restaurant_owned(self, merchant_id: uuid.UUID, restaurant_id: uuid.UUID) -> None:
        if self.restaurant_repo.get_owned(restaurant_id, merchant_id) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Restaurant not found")
