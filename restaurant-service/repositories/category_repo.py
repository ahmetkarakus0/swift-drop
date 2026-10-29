import uuid
from typing import Optional

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, selectinload

from models import Category, Restaurant


class CategoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_owned(self, category_id: int, merchant_id: uuid.UUID) -> Optional[Category]:
        return self.db.scalar(self._owned_query(category_id, merchant_id))

    def get_owned_with_items(self, category_id: int, merchant_id: uuid.UUID) -> Optional[Category]:
        return self.db.scalar(
            self._owned_query(category_id, merchant_id).options(selectinload(Category.items))
        )

    @staticmethod
    def _owned_query(category_id: int, merchant_id: uuid.UUID) -> Select[tuple[Category]]:
        return (
            select(Category)
            .join(Category.restaurant)
            .where(
                Category.id == category_id,
                Restaurant.merchant_id == merchant_id,
                Restaurant.is_active.is_(True),
            )
        )

    def list_by_restaurant(self, restaurant_id: uuid.UUID) -> list[Category]:
        return list(
            self.db.scalars(
                select(Category)
                .where(Category.restaurant_id == restaurant_id)
                .order_by(Category.id)
            )
        )

    def create(self, category: Category) -> Category:
        self.db.add(category)
        self.db.commit()
        return category

    def save(self, category: Category) -> Category:
        self.db.commit()
        return category

    def delete(self, category: Category) -> None:
        self.db.delete(category)
        self.db.commit()
