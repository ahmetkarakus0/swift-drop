"""Ready-made restaurant menus for case tests, built through restaurant-service's API."""

from dataclasses import dataclass
from typing import Any

from framework import data
from framework.actors import Actor
from framework.http_client import expect_status
from framework.services import RestaurantServiceApi


@dataclass
class Menu:
    restaurant: dict[str, Any]
    category: dict[str, Any]
    items: list[dict[str, Any]]

    @property
    def restaurant_id(self) -> str:
        return self.restaurant["id"]

    @property
    def item(self) -> dict[str, Any]:
        return self.items[0]


class Menus:
    def __init__(self, restaurant_api: RestaurantServiceApi):
        self.restaurant_api = restaurant_api

    def create(self, merchant: Actor, *, is_open: bool = True, prices: tuple[str, ...] = ("99.90",)) -> Menu:
        """One restaurant with one category holding an item per price."""
        token = merchant.access_token
        restaurant = expect_status(
            self.restaurant_api.create_restaurant(token, data.restaurant_payload(is_open=is_open)), 201
        ).json()
        category = expect_status(
            self.restaurant_api.create_category(token, restaurant["id"], data.category_payload()), 201
        ).json()
        items = [
            expect_status(
                self.restaurant_api.create_item(token, category["id"], data.item_payload(price=price)), 201
            ).json()
            for price in prices
        ]
        return Menu(restaurant=restaurant, category=category, items=items)
