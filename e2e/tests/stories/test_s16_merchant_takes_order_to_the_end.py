from decimal import Decimal

import pytest

from framework import data
from framework.http_client import expect_status


def _order_status(order_db, order_id: str) -> str:
    return order_db.scalar("SELECT status FROM orders WHERE id = :id", id=order_id)


def _place_order(order_api, customer, item_id: int, quantity: int) -> tuple[dict, dict]:
    basket = expect_status(order_api.add_basket_item(customer.access_token, item_id, quantity), 201).json()
    order = expect_status(
        order_api.place_order(customer.access_token, data.order_payload(basket["id"])), 201
    ).json()
    return basket, order


@pytest.mark.story
def test_merchant_hands_one_order_to_pickup_and_cancels_another(actors, menus, restaurant_api, order_api, order_db):
    merchant = actors.merchant()
    menu = menus.create(merchant, prices=("45.50",))
    customer = actors.customer()
    token, restaurant_id, item = merchant.access_token, menu.restaurant_id, menu.item

    basket, order = _place_order(order_api, customer, item["id"], 2)
    assert basket["restaurant_id"] == restaurant_id
    assert Decimal(basket["total_price"]) == Decimal("91.00")
    assert order["status"] == "pending"
    assert order["user_id"] == customer.user_id
    assert Decimal(order["total_price"]) == Decimal("91.00")
    assert [(i["item_id"], i["quantity"]) for i in order["items"]] == [(item["id"], 2)]
    assert order_db.scalar("SELECT count(*) FROM baskets WHERE id = :id", id=basket["id"]) == 0

    orders = expect_status(restaurant_api.list_orders(token, restaurant_id), 200).json()
    assert [o["id"] for o in orders] == [order["id"]]

    for action, expected_status in (
        (restaurant_api.accept_order, "confirmed"),
        (restaurant_api.prepare_order, "preparing"),
        (restaurant_api.mark_order_ready_for_pickup, "ready_for_pickup"),
    ):
        updated = expect_status(action(token, restaurant_id, order["id"]), 200).json()
        assert updated["status"] == expected_status
        assert _order_status(order_db, order["id"]) == expected_status

    response = expect_status(restaurant_api.cancel_order(token, restaurant_id, order["id"]), 409)
    assert "ready_for_pickup" in response.json()["detail"]
    assert _order_status(order_db, order["id"]) == "ready_for_pickup"

    _, second = _place_order(order_api, customer, item["id"], 1)
    expect_status(restaurant_api.accept_order(token, restaurant_id, second["id"]), 200)
    expect_status(restaurant_api.prepare_order(token, restaurant_id, second["id"]), 200)
    cancelled = expect_status(restaurant_api.cancel_order(token, restaurant_id, second["id"]), 200).json()
    assert cancelled["status"] == "cancelled"

    expect_status(restaurant_api.mark_order_ready_for_pickup(token, restaurant_id, second["id"]), 409)
    assert _order_status(order_db, second["id"]) == "cancelled"

    statuses = {o["id"]: o["status"] for o in expect_status(restaurant_api.list_orders(token, restaurant_id), 200).json()}
    assert statuses == {order["id"]: "ready_for_pickup", second["id"]: "cancelled"}
