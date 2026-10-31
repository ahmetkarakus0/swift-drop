import uuid

from fastapi import HTTPException, status

from models import Order, OrderItem
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
