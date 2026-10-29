import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Category, Restaurant


class CategoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_owned(self, category_id: int, merchant_id: uuid.UUID) -> Optional[Category]:
        return self.db.scalar(
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
