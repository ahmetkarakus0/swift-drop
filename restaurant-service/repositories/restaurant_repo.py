import uuid
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from models import Category, Item, Restaurant


class RestaurantRepository:
    """Only active restaurants are visible; an inactive restaurant is treated as deleted."""

    def __init__(self, db: Session):
        self.db = db

    def get_owned(self, restaurant_id: uuid.UUID, merchant_id: uuid.UUID) -> Optional[Restaurant]:
        return self.db.scalar(
            select(Restaurant).where(
                Restaurant.id == restaurant_id,
                Restaurant.merchant_id == merchant_id,
                Restaurant.is_active.is_(True),
            )
        )

    def list_by_merchant(self, merchant_id: uuid.UUID) -> list[Restaurant]:
        return list(
            self.db.scalars(
                select(Restaurant)
                .where(Restaurant.merchant_id == merchant_id, Restaurant.is_active.is_(True))
                .order_by(Restaurant.created_at)
            )
        )

    def create(self, restaurant: Restaurant) -> Restaurant:
        self.db.add(restaurant)
        self.db.commit()
        return restaurant

    def save(self, restaurant: Restaurant) -> Restaurant:
        self.db.commit()
        return restaurant

    def deactivate(self, restaurant: Restaurant) -> None:
        """Soft-deletes the restaurant together with its categories and items in one transaction."""
        category_ids = select(Category.id).where(Category.restaurant_id == restaurant.id)
        self.db.execute(
            update(Item).where(Item.category_id.in_(category_ids)).values(is_active=False)
        )
        self.db.execute(
            update(Category).where(Category.restaurant_id == restaurant.id).values(is_active=False)
        )
        restaurant.is_active = False
        self.db.commit()
