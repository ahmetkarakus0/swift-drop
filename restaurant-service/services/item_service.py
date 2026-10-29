import uuid

from fastapi import HTTPException, status

from models import Item
from repositories.category_repo import CategoryRepository
from repositories.item_repo import ItemRepository
from schemas.item_schema import ItemCreate, ItemUpdate


class ItemService:
    def __init__(self, category_repo: CategoryRepository, item_repo: ItemRepository):
        self.category_repo = category_repo
        self.item_repo = item_repo

    def create(self, merchant_id: uuid.UUID, category_id: int, data: ItemCreate) -> Item:
        self._ensure_category_owned(merchant_id, category_id)
        return self.item_repo.create(Item(**data.model_dump(), category_id=category_id))

    def get_all(self, merchant_id: uuid.UUID, category_id: int) -> list[Item]:
        self._ensure_category_owned(merchant_id, category_id)
        return self.item_repo.list_by_category(category_id)

    def get(self, merchant_id: uuid.UUID, item_id: int) -> Item:
        item = self.item_repo.get_owned(item_id, merchant_id)
        if item is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Item not found")
        return item

    def update(self, merchant_id: uuid.UUID, item_id: int, data: ItemUpdate) -> Item:
        item = self.get(merchant_id, item_id)
        for field, value in data.changes().items():
            setattr(item, field, value)
        return self.item_repo.save(item)

    def delete(self, merchant_id: uuid.UUID, item_id: int) -> None:
        self.item_repo.delete(self.get(merchant_id, item_id))

    def _ensure_category_owned(self, merchant_id: uuid.UUID, category_id: int) -> None:
        if self.category_repo.get_owned(category_id, merchant_id) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Category not found")
