"""A merchant only sees and changes its own restaurants, categories and items.

Two approved merchants each build a menu. Lists only return the caller's own records;
reading or changing the other merchant's records returns 404 (existence isn't leaked)
and leaves the database untouched.
"""

from dataclasses import dataclass

import pytest

from framework import data
from framework.actors import Actor, Actors
from framework.db import Database
from framework.http_client import expect_status
from framework.services import RestaurantServiceApi


@dataclass
class Menu:
    merchant: Actor
    restaurant_id: str
    category_id: int
    item_id: int


def _build_menu(restaurant_api: RestaurantServiceApi, merchant: Actor) -> Menu:
    token = merchant.access_token
    restaurant = expect_status(restaurant_api.create_restaurant(token, data.restaurant_payload()), 201).json()
    category = expect_status(
        restaurant_api.create_category(token, restaurant["id"], data.category_payload()), 201
    ).json()
    item = expect_status(restaurant_api.create_item(token, category["id"], data.item_payload()), 201).json()
    return Menu(merchant, restaurant["id"], category["id"], item["id"])


@pytest.fixture
def menus(actors: Actors, restaurant_api: RestaurantServiceApi) -> tuple[Menu, Menu]:
    return _build_menu(restaurant_api, actors.merchant()), _build_menu(restaurant_api, actors.merchant())


def _snapshot(restaurant_db: Database, menu: Menu) -> dict:
    return {
        "restaurant": restaurant_db.fetch_one(
            "SELECT name, is_active FROM restaurants WHERE id = :id", id=menu.restaurant_id
        ),
        "categories": restaurant_db.fetch_all(
            "SELECT id, name, is_active FROM categories WHERE restaurant_id = :id ORDER BY id",
            id=menu.restaurant_id,
        ),
        "items": restaurant_db.fetch_all(
            "SELECT id, name, is_active FROM items WHERE category_id = :id ORDER BY id", id=menu.category_id
        ),
    }


@pytest.mark.restaurant_service
def test_lists_only_contain_own_records(menus: tuple[Menu, Menu], restaurant_api: RestaurantServiceApi):
    for own in menus:
        token = own.merchant.access_token

        restaurants = expect_status(restaurant_api.list_restaurants(token), 200).json()
        assert [r["id"] for r in restaurants] == [own.restaurant_id]
        assert all(r["merchant_id"] == own.merchant.profile_id for r in restaurants)

        detail = expect_status(restaurant_api.get_restaurant(token, own.restaurant_id), 200).json()
        assert [c["id"] for c in detail["categories"]] == [own.category_id]
        assert [i["id"] for i in detail["categories"][0]["items"]] == [own.item_id]

        categories = expect_status(restaurant_api.list_categories(token, own.restaurant_id), 200).json()
        assert [c["id"] for c in categories] == [own.category_id]

        items = expect_status(restaurant_api.list_items(token, own.category_id), 200).json()
        assert [i["id"] for i in items] == [own.item_id]


@pytest.mark.restaurant_service
def test_cannot_read_other_merchants_records(menus: tuple[Menu, Menu], restaurant_api: RestaurantServiceApi):
    own, other = menus
    token = own.merchant.access_token

    requests = {
        "get restaurant": restaurant_api.get_restaurant(token, other.restaurant_id),
        "list categories": restaurant_api.list_categories(token, other.restaurant_id),
        "get category": restaurant_api.get_category(token, other.category_id),
        "list items": restaurant_api.list_items(token, other.category_id),
        "get item": restaurant_api.get_item(token, other.item_id),
    }
    for name, response in requests.items():
        assert response.status_code == 404, f"{name}: {response.status_code} {response.text}"


@pytest.mark.restaurant_service
def test_cannot_change_other_merchants_records(
    menus: tuple[Menu, Menu], restaurant_api: RestaurantServiceApi, restaurant_db: Database
):
    own, other = menus
    token = own.merchant.access_token
    before = _snapshot(restaurant_db, other)

    requests = {
        "update restaurant": restaurant_api.update_restaurant(
            token, other.restaurant_id, {"name": data.unique_name("Hijacked")}
        ),
        "create category": restaurant_api.create_category(token, other.restaurant_id, data.category_payload()),
        "update category": restaurant_api.update_category(
            token, other.category_id, {"name": data.unique_name("Hijacked")}
        ),
        "create item": restaurant_api.create_item(token, other.category_id, data.item_payload()),
        "update item": restaurant_api.update_item(token, other.item_id, {"name": data.unique_name("Hijacked")}),
        "delete item": restaurant_api.delete_item(token, other.item_id),
        "delete category": restaurant_api.delete_category(token, other.category_id),
        "delete restaurant": restaurant_api.delete_restaurant(token, other.restaurant_id),
    }
    for name, response in requests.items():
        assert response.status_code == 404, f"{name}: {response.status_code} {response.text}"

    assert _snapshot(restaurant_db, other) == before

    other_token = other.merchant.access_token
    detail = expect_status(restaurant_api.get_restaurant(other_token, other.restaurant_id), 200).json()
    assert [c["id"] for c in detail["categories"]] == [other.category_id]
    assert [i["id"] for i in detail["categories"][0]["items"]] == [other.item_id]
