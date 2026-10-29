import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Category, Item, Restaurant


class ItemRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_owned(self, item_id: int, merchant_id: uuid.UUID) -> Optional[Item]:
        return self.db.scalar(
            select(Item)
            .join(Item.category)
            .join(Category.restaurant)
            .where(
                Item.id == item_id,
                Restaurant.merchant_id == merchant_id,
                Restaurant.is_active.is_(True),
            )
        )

    def list_by_category(self, category_id: int) -> list[Item]:
        return list(
            self.db.scalars(
                select(Item).where(Item.category_id == category_id).order_by(Item.id)
            )
        )

    def create(self, item: Item) -> Item:
        self.db.add(item)
        self.db.commit()
        return item

    def save(self, item: Item) -> Item:
        self.db.commit()
        return item

    def delete(self, item: Item) -> None:
        self.db.delete(item)
        self.db.commit()
