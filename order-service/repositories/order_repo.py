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

    def list_unassigned_ready_for_pickup(self, restaurant_ids: list[uuid.UUID]) -> list[Order]:
        query = (
            select(Order)
            .where(
                Order.restaurant_id.in_(restaurant_ids),
                Order.status == OrderStatus.READY_FOR_PICKUP,
                Order.courier_id.is_(None),
            )
            .options(selectinload(Order.items))
            .order_by(Order.updated_at.asc())
        )
        return list(self.db.scalars(query))

    def get_by_restaurant_for_update(
        self, order_id: uuid.UUID, restaurant_id: uuid.UUID
    ) -> Optional[Order]:
        return self.db.scalar(
            select(Order)
            .where(Order.id == order_id, Order.restaurant_id == restaurant_id)
            .options(selectinload(Order.items))
            .with_for_update()
        )

    def save(self, order: Order) -> Order:
        self.db.commit()
        return order

    def create_from_basket(self, order: Order, basket: Basket) -> Order:
        self.db.add(order)
        self.db.delete(basket)
        self.db.commit()
        return order
