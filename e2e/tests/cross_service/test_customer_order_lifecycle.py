from decimal import Decimal

import pytest

from framework import data
from framework.http_client import expect_status


def _order_status(order_db, order_id: str) -> str:
    return order_db.scalar("SELECT status FROM orders WHERE id = :id", id=order_id)


def _place_order(order_api, customer, item_id: int, quantity: int) -> dict:
    basket = expect_status(order_api.add_basket_item(customer.access_token, item_id, quantity), 201).json()
    return expect_status(
        order_api.place_order(customer.access_token, data.order_payload(basket["id"])), 201
    ).json()


@pytest.mark.cross_service
def test_customer_orders_and_merchant_moves_order_through_statuses(
    actors, restaurant_api, order_api, user_db, order_db
):
    customer = actors.customer()
    merchant = actors.merchant()
    assert user_db.scalar("SELECT is_verified FROM users WHERE id = :id", id=customer.user_id) is True
    assert user_db.scalar("SELECT is_verified FROM merchants WHERE id = :id", id=merchant.profile_id) is True

    restaurant = expect_status(
        restaurant_api.create_restaurant(merchant.access_token, data.restaurant_payload(is_open=True)), 201
    ).json()
    category = expect_status(
        restaurant_api.create_category(merchant.access_token, restaurant["id"], data.category_payload()), 201
    ).json()
    item_payload = data.item_payload()
    item = expect_status(
        restaurant_api.create_item(merchant.access_token, category["id"], item_payload), 201
    ).json()

    basket = expect_status(order_api.add_basket_item(customer.access_token, item["id"], 2), 201).json()
    assert basket["restaurant_id"] == restaurant["id"]
    assert len(basket["items"]) == 1
    assert basket["items"][0]["item_id"] == item["id"]
    assert basket["items"][0]["quantity"] == 2
    assert Decimal(basket["total_price"]) == Decimal(item_payload["price"]) * 2

    order = expect_status(
        order_api.place_order(customer.access_token, data.order_payload(basket["id"])), 201
    ).json()
    assert order["status"] == "pending"
    assert order["user_id"] == customer.user_id
    assert order["restaurant_id"] == restaurant["id"]
    assert Decimal(order["total_price"]) == Decimal(item_payload["price"]) * 2
    assert [(i["item_id"], i["quantity"]) for i in order["items"]] == [(item["id"], 2)]
    assert order_db.scalar("SELECT count(*) FROM baskets WHERE id = :id", id=basket["id"]) == 0
    assert _order_status(order_db, order["id"]) == "pending"

    orders = expect_status(restaurant_api.list_orders(merchant.access_token, restaurant["id"]), 200).json()
    assert [o["id"] for o in orders] == [order["id"]]

    token, restaurant_id, order_id = merchant.access_token, restaurant["id"], order["id"]
    steps = [
        (restaurant_api.accept_order, "confirmed"),
        (restaurant_api.prepare_order, "preparing"),
        (restaurant_api.mark_order_ready_for_pickup, "ready_for_pickup"),
    ]
    for action, expected_status in steps:
        updated = expect_status(action(token, restaurant_id, order_id), 200).json()
        assert updated["status"] == expected_status
        assert _order_status(order_db, order_id) == expected_status

    response = expect_status(restaurant_api.cancel_order(token, restaurant_id, order_id), 409)
    assert "ready_for_pickup" in response.json()["detail"]
    assert _order_status(order_db, order_id) == "ready_for_pickup"

    second = _place_order(order_api, customer, item["id"], 1)
    assert second["status"] == "pending"
    expect_status(restaurant_api.accept_order(token, restaurant_id, second["id"]), 200)
    expect_status(restaurant_api.prepare_order(token, restaurant_id, second["id"]), 200)
    cancelled = expect_status(restaurant_api.cancel_order(token, restaurant_id, second["id"]), 200).json()
    assert cancelled["status"] == "cancelled"
    assert _order_status(order_db, second["id"]) == "cancelled"

    expect_status(restaurant_api.mark_order_ready_for_pickup(token, restaurant_id, second["id"]), 409)
    assert _order_status(order_db, second["id"]) == "cancelled"

    statuses = {
        o["id"]: o["status"]
        for o in expect_status(restaurant_api.list_orders(token, restaurant_id), 200).json()
    }
    assert statuses == {order_id: "ready_for_pickup", second["id"]: "cancelled"}
