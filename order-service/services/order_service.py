import uuid
from typing import Optional

from fastapi import HTTPException, status

from models import Order, OrderItem, OrderStatus
from repositories.basket_repo import BasketRepository
from repositories.order_repo import OrderRepository
from schemas.order_schema import OrderCreate
from services.event_publisher import OrderEventPublisher


class OrderService:
    def __init__(
        self,
        basket_repo: BasketRepository,
        order_repo: OrderRepository,
        event_publisher: OrderEventPublisher,
    ):
        self.basket_repo = basket_repo
        self.order_repo = order_repo
        self.event_publisher = event_publisher

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
        order = self.order_repo.create_from_basket(order, basket)
        self.event_publisher.order_created(order)
        return order

    def get_all_for_restaurant(
        self, restaurant_id: uuid.UUID, order_status: Optional[OrderStatus] = None
    ) -> list[Order]:
        return self.order_repo.list_by_restaurant(restaurant_id, order_status)

    def get_unassigned_ready_for_pickup(self, restaurant_ids: list[uuid.UUID]) -> list[Order]:
        if not restaurant_ids:
            return []
        return self.order_repo.list_unassigned_ready_for_pickup(restaurant_ids)

    def assign_courier(self, order_id: uuid.UUID, courier_id: uuid.UUID) -> Order:
        """Assigns a courier to a ready for pickup order; repeating it for the same courier is a no-op."""
        order = self.order_repo.get_for_update(order_id)
        if order is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
        if order.courier_id == courier_id:
            return order
        if order.courier_id is not None:
            raise HTTPException(status.HTTP_409_CONFLICT, "Order already has a courier")
        if order.status != OrderStatus.READY_FOR_PICKUP:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"Only ready_for_pickup orders can be assigned; order is {order.status.value}",
            )
        order.courier_id = courier_id
        order = self.order_repo.save(order)
        self.event_publisher.courier_assigned(order)
        return order

    def mark_on_the_way(self, courier_id: uuid.UUID, order_id: uuid.UUID) -> Order:
        order = self.order_repo.get_by_courier_for_update(order_id, courier_id)
        return self._change_status(
            order, (OrderStatus.READY_FOR_PICKUP,), OrderStatus.ON_THE_WAY, "marked on the way"
        )

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
        return self._change_status(order, from_statuses, to_status, action)

    def _change_status(
        self,
        order: Optional[Order],
        from_statuses: tuple[OrderStatus, ...],
        to_status: OrderStatus,
        action: str,
    ) -> Order:
        if order is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
        if order.status not in from_statuses:
            allowed = ", ".join(s.value for s in from_statuses)
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"Only {allowed} orders can be {action}; order is {order.status.value}",
            )
        previous_status = order.status
        order.status = to_status
        order = self.order_repo.save(order)
        self.event_publisher.order_status_updated(order, previous_status)
        return order
