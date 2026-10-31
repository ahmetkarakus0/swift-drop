import uuid
from typing import Optional

from fastapi import HTTPException, status

from models import Order, OrderItem, OrderStatus
from repositories.basket_repo import BasketRepository
from repositories.order_repo import OrderRepository
from schemas.order_schema import OrderCreate


class OrderService:
    def __init__(self, basket_repo: BasketRepository, order_repo: OrderRepository):
        self.basket_repo = basket_repo
        self.order_repo = order_repo

    def place(self, user_id: uuid.UUID, data: OrderCreate) -> Order:
        basket = self.basket_repo.get_owned_for_update(data.basket_id, user_id)
        if basket is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Basket not found")
        if not basket.items:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Basket is empty")

        items = [
            OrderItem(
                item_id=basket_item.item_id,
                item_name=basket_item.item_name,
                quantity=basket_item.quantity,
                price=basket_item.price,
            )
            for basket_item in basket.items
        ]
        order = Order(
            user_id=user_id,
            restaurant_id=basket.restaurant_id,
            total_price=sum((item.price * item.quantity for item in items)),
            delivery_address=data.delivery_address,
            items=items,
        )
        return self.order_repo.create_from_basket(order, basket)

    def get_all_for_restaurant(
        self, restaurant_id: uuid.UUID, order_status: Optional[OrderStatus] = None
    ) -> list[Order]:
        return self.order_repo.list_by_restaurant(restaurant_id, order_status)

    def accept(self, restaurant_id: uuid.UUID, order_id: uuid.UUID) -> Order:
        return self._transition(
            restaurant_id, order_id, (OrderStatus.PENDING,), OrderStatus.CONFIRMED, "accepted"
        )

    def prepare(self, restaurant_id: uuid.UUID, order_id: uuid.UUID) -> Order:
        return self._transition(
            restaurant_id, order_id, (OrderStatus.CONFIRMED,), OrderStatus.PREPARING, "prepared"
        )

    def mark_ready_for_pickup(self, restaurant_id: uuid.UUID, order_id: uuid.UUID) -> Order:
        return self._transition(
            restaurant_id,
            order_id,
            (OrderStatus.PREPARING,),
            OrderStatus.READY_FOR_PICKUP,
            "marked ready for pickup",
        )

    def cancel(self, restaurant_id: uuid.UUID, order_id: uuid.UUID) -> Order:
        return self._transition(
            restaurant_id,
            order_id,
            (OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.PREPARING),
            OrderStatus.CANCELLED,
            "cancelled",
        )

    def _transition(
        self,
        restaurant_id: uuid.UUID,
        order_id: uuid.UUID,
        from_statuses: tuple[OrderStatus, ...],
        to_status: OrderStatus,
        action: str,
    ) -> Order:
        order = self.order_repo.get_by_restaurant_for_update(order_id, restaurant_id)
        if order is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
        if order.status not in from_statuses:
            allowed = ", ".join(s.value for s in from_statuses)
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"Only {allowed} orders can be {action}; order is {order.status.value}",
            )
        order.status = to_status
        return self.order_repo.save(order)
