import uuid
from typing import Optional

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, selectinload

from models import Basket, BasketItem


class BasketRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_owned(self, basket_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Basket]:
        return self.db.scalar(self._owned_query(basket_id, user_id))

    def get_owned_for_update(self, basket_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Basket]:
        return self.db.scalar(self._owned_query(basket_id, user_id).with_for_update())

    def get_by_restaurant(self, user_id: uuid.UUID, restaurant_id: uuid.UUID) -> Optional[Basket]:
        return self.db.scalar(
            select(Basket)
            .where(Basket.user_id == user_id, Basket.restaurant_id == restaurant_id)
            .options(selectinload(Basket.items))
        )

    def list_by_user(self, user_id: uuid.UUID) -> list[Basket]:
        return list(
            self.db.scalars(
                select(Basket)
                .where(Basket.user_id == user_id)
                .options(selectinload(Basket.items))
                .order_by(Basket.created_at)
            )
        )

    @staticmethod
    def _owned_query(basket_id: uuid.UUID, user_id: uuid.UUID) -> Select[tuple[Basket]]:
        return (
            select(Basket)
            .where(Basket.id == basket_id, Basket.user_id == user_id)
            .options(selectinload(Basket.items))
        )

    def add(self, basket: Basket) -> None:
        self.db.add(basket)

    def save(self, basket: Basket) -> Basket:
        self.db.commit()
        return basket

    def delete(self, basket: Basket) -> None:
        self.db.delete(basket)
        self.db.commit()

    def delete_item(self, item: BasketItem) -> None:
        self.db.delete(item)
        self.db.commit()
