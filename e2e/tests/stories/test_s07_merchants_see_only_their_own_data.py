from decimal import Decimal

import pytest

from framework import data
from framework.http_client import expect_status


def _order_from(order_api, customer, item_id: int) -> dict:
    basket = expect_status(order_api.add_basket_item(customer.access_token, item_id), 201).json()
    return expect_status(
        order_api.place_order(customer.access_token, data.order_payload(basket["id"])), 201
    ).json()


@pytest.mark.story
def test_two_merchants_each_manage_only_their_own_restaurant_and_orders(
    actors, menus, restaurant_api, order_api, order_db, restaurant_db
):
    merchant_a, merchant_b = actors.merchant(), actors.merchant()
    menu_a, menu_b = menus.create(merchant_a), menus.create(merchant_b)
    customer = actors.customer()

    order_a = _order_from(order_api, customer, menu_a.item["id"])
    order_b = _order_from(order_api, customer, menu_b.item["id"])

    orders = expect_status(restaurant_api.list_orders(merchant_a.access_token, menu_a.restaurant_id), 200).json()
    assert [o["id"] for o in orders] == [order_a["id"]]
    orders = expect_status(restaurant_api.list_orders(merchant_b.access_token, menu_b.restaurant_id), 200).json()
    assert [o["id"] for o in orders] == [order_b["id"]]

    b_token = merchant_b.access_token
    expect_status(restaurant_api.list_orders(b_token, menu_a.restaurant_id), 404)
    expect_status(restaurant_api.accept_order(b_token, menu_a.restaurant_id, order_a["id"]), 404)
    response = expect_status(restaurant_api.accept_order(b_token, menu_b.restaurant_id, order_a["id"]), 404)
    assert response.json()["detail"] == "Order not found"
    expect_status(restaurant_api.cancel_order(b_token, menu_b.restaurant_id, order_a["id"]), 404)
    expect_status(restaurant_api.update_item(b_token, menu_a.item["id"], {"price": "1.00"}), 404)
    expect_status(restaurant_api.update_restaurant(b_token, menu_a.restaurant_id, {"is_open": False}), 404)

    assert order_db.scalar("SELECT status FROM orders WHERE id = :id", id=order_a["id"]) == "pending"
    assert restaurant_db.scalar("SELECT price FROM items WHERE id = :id", id=menu_a.item["id"]) == Decimal(
        menu_a.item["price"]
    )
    assert restaurant_db.scalar("SELECT is_open FROM restaurants WHERE id = :id", id=menu_a.restaurant_id) is True

    accepted = expect_status(
        restaurant_api.accept_order(merchant_a.access_token, menu_a.restaurant_id, order_a["id"]), 200
    ).json()
    assert accepted["status"] == "confirmed"
    assert order_db.scalar("SELECT status FROM orders WHERE id = :id", id=order_b["id"]) == "pending"
