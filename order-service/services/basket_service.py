import uuid

from fastapi import HTTPException, status

from models import Basket, BasketItem
from repositories.basket_repo import BasketRepository
from schemas.basket_schema import BasketItemCreate, BasketItemUpdate
from services.catalog_service import CatalogService


class BasketService:
    def __init__(self, basket_repo: BasketRepository, catalog_service: CatalogService):
        self.basket_repo = basket_repo
        self.catalog_service = catalog_service

    def add_item(self, user_id: uuid.UUID, data: BasketItemCreate) -> Basket:
        catalog_item = self.catalog_service.get_item(data.item_id)
        if not catalog_item.restaurant_is_open:
            raise HTTPException(status.HTTP_409_CONFLICT, "Restaurant is closed")

        basket = self.basket_repo.get_by_restaurant(user_id, catalog_item.restaurant_id)
        if basket is None:
            basket = Basket(user_id=user_id, restaurant_id=catalog_item.restaurant_id, items=[])
            self.basket_repo.add(basket)

        basket_item = next((i for i in basket.items if i.item_id == catalog_item.id), None)
        if basket_item is None:
            basket.items.append(
                BasketItem(
                    item_id=catalog_item.id,
                    item_name=catalog_item.name,
                    quantity=data.quantity,
                    price=catalog_item.price,
                )
            )
        else:
            basket_item.quantity = min(basket_item.quantity + data.quantity, 99)
            basket_item.item_name = catalog_item.name
            basket_item.price = catalog_item.price
        return self.basket_repo.save(basket)

    def get_all(self, user_id: uuid.UUID) -> list[Basket]:
        return self.basket_repo.list_by_user(user_id)

    def get(self, user_id: uuid.UUID, basket_id: uuid.UUID) -> Basket:
        basket = self.basket_repo.get_owned(basket_id, user_id)
        if basket is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Basket not found")
        return basket

    def update_item(
        self,
        user_id: uuid.UUID,
        basket_id: uuid.UUID,
        basket_item_id: uuid.UUID,
        data: BasketItemUpdate,
    ) -> Basket:
        basket = self.get(user_id, basket_id)
        self._get_item(basket, basket_item_id).quantity = data.quantity
        return self.basket_repo.save(basket)

    def remove_item(
        self, user_id: uuid.UUID, basket_id: uuid.UUID, basket_item_id: uuid.UUID
    ) -> None:
        basket = self.get(user_id, basket_id)
        basket_item = self._get_item(basket, basket_item_id)
        if len(basket.items) == 1:
            self.basket_repo.delete(basket)
        else:
            self.basket_repo.delete_item(basket_item)

    def delete(self, user_id: uuid.UUID, basket_id: uuid.UUID) -> None:
        self.basket_repo.delete(self.get(user_id, basket_id))

    @staticmethod
    def _get_item(basket: Basket, basket_item_id: uuid.UUID) -> BasketItem:
        basket_item = next((i for i in basket.items if i.id == basket_item_id), None)
        if basket_item is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Basket item not found")
        return basket_item
