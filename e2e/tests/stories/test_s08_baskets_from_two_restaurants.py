from decimal import Decimal

import pytest

from framework import data
from framework.http_client import expect_status


def _baskets_by_restaurant(order_api, token: str) -> dict[str, dict]:
    return {b["restaurant_id"]: b for b in expect_status(order_api.list_baskets(token), 200).json()}


@pytest.mark.story
def test_customer_fills_two_baskets_and_orders_them_separately(actors, menus, restaurant_api, order_api):
    merchant_a, merchant_b = actors.merchant(), actors.merchant()
    menu_a = menus.create(merchant_a, prices=("40.00", "25.00"))
    menu_b = menus.create(merchant_b, prices=("60.00",))
    pizza, salad = menu_a.items
    kebab = menu_b.item
    customer = actors.customer()
    token = customer.access_token

    expect_status(order_api.add_basket_item(token, pizza["id"]), 201)
    expect_status(order_api.add_basket_item(token, salad["id"], 2), 201)
    expect_status(order_api.add_basket_item(token, kebab["id"]), 201)

    baskets = _baskets_by_restaurant(order_api, token)
    assert set(baskets) == {menu_a.restaurant_id, menu_b.restaurant_id}
    basket_a, basket_b = baskets[menu_a.restaurant_id], baskets[menu_b.restaurant_id]
    lines = {i["item_id"]: i for i in basket_a["items"]}
    assert Decimal(basket_a["total_price"]) == Decimal("90.00")

    expect_status(order_api.update_basket_item(token, basket_a["id"], lines[pizza["id"]]["id"], 3), 200)
    expect_status(order_api.remove_basket_item(token, basket_a["id"], lines[salad["id"]]["id"]), 204)
    basket_a = expect_status(order_api.get_basket(token, basket_a["id"]), 200).json()
    assert [(i["item_id"], i["quantity"]) for i in basket_a["items"]] == [(pizza["id"], 3)]
    assert Decimal(basket_a["total_price"]) == Decimal("120.00")

    order_a = expect_status(order_api.place_order(token, data.order_payload(basket_a["id"])), 201).json()
    assert Decimal(order_a["total_price"]) == Decimal("120.00")

    baskets = _baskets_by_restaurant(order_api, token)
    assert set(baskets) == {menu_b.restaurant_id}
    assert baskets[menu_b.restaurant_id]["id"] == basket_b["id"]

    orders_a = expect_status(restaurant_api.list_orders(merchant_a.access_token, menu_a.restaurant_id), 200).json()
    assert [(o["id"], [(i["item_id"], i["quantity"]) for i in o["items"]]) for o in orders_a] == [
        (order_a["id"], [(pizza["id"], 3)])
    ]
    assert expect_status(restaurant_api.list_orders(merchant_b.access_token, menu_b.restaurant_id), 200).json() == []

    order_b = expect_status(order_api.place_order(token, data.order_payload(basket_b["id"])), 201).json()
    assert Decimal(order_b["total_price"]) == Decimal("60.00")
    assert expect_status(order_api.list_baskets(token), 200).json() == []

    orders_b = expect_status(restaurant_api.list_orders(merchant_b.access_token, menu_b.restaurant_id), 200).json()
    assert [o["id"] for o in orders_b] == [order_b["id"]]
    orders_a = expect_status(restaurant_api.list_orders(merchant_a.access_token, menu_a.restaurant_id), 200).json()
    assert [o["id"] for o in orders_a] == [order_a["id"]]
