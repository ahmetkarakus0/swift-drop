import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from models import Basket, Order, OrderStatus


class OrderRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_by_restaurant(
        self, restaurant_id: uuid.UUID, status: Optional[OrderStatus] = None
    ) -> list[Order]:
        query = (
            select(Order)
            .where(Order.restaurant_id == restaurant_id)
            .options(selectinload(Order.items))
            .order_by(Order.created_at.desc())
        )
        if status is not None:
            query = query.where(Order.status == status)
        return list(self.db.scalars(query))

    def create_from_basket(self, order: Order, basket: Basket) -> Order:
        self.db.add(order)
        self.db.delete(basket)
        self.db.commit()
        return order
