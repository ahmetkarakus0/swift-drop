import pytest

from framework import data
from framework.http_client import expect_status


@pytest.mark.story
def test_customer_can_order_only_while_restaurant_is_open(actors, menus, restaurant_api, order_api, order_db):
    merchant = actors.merchant()
    menu = menus.create(merchant, is_open=False)
    assert menu.restaurant["is_open"] is False
    customer = actors.customer()
    item_id = menu.item["id"]

    response = expect_status(order_api.add_basket_item(customer.access_token, item_id), 409)
    assert response.json()["detail"] == "Restaurant is closed"
    assert order_db.scalar("SELECT count(*) FROM baskets WHERE user_id = :id", id=customer.user_id) == 0

    opened = expect_status(
        restaurant_api.update_restaurant(merchant.access_token, menu.restaurant_id, {"is_open": True}), 200
    ).json()
    assert opened["is_open"] is True

    basket = expect_status(order_api.add_basket_item(customer.access_token, item_id), 201).json()
    order = expect_status(
        order_api.place_order(customer.access_token, data.order_payload(basket["id"])), 201
    ).json()
    assert order["restaurant_id"] == menu.restaurant_id

    orders = expect_status(restaurant_api.list_orders(merchant.access_token, menu.restaurant_id), 200).json()
    assert [o["id"] for o in orders] == [order["id"]]

    expect_status(restaurant_api.update_restaurant(merchant.access_token, menu.restaurant_id, {"is_open": False}), 200)

    response = expect_status(order_api.add_basket_item(customer.access_token, item_id), 409)
    assert response.json()["detail"] == "Restaurant is closed"
    assert order_db.scalar("SELECT count(*) FROM baskets WHERE user_id = :id", id=customer.user_id) == 0
