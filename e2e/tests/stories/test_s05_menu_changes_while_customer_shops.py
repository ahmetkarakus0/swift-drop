from decimal import Decimal

import pytest

from framework import data
from framework.http_client import expect_status


def _place(order_api, customer, basket_id: str) -> dict:
    return expect_status(order_api.place_order(customer.access_token, data.order_payload(basket_id)), 201).json()


@pytest.mark.story
def test_menu_changes_after_items_are_in_the_basket(actors, menus, restaurant_api, order_api, order_db):
    """Pins current behaviour: baskets keep the name and price from when the item was added, and placing
    an order doesn't ask restaurant-service again. Only adding an item re-reads the menu."""
    merchant = actors.merchant()
    menu = menus.create(merchant, prices=("50.00", "30.00"))
    burger, fries = menu.items
    customer = actors.customer()
    token, merchant_token = customer.access_token, merchant.access_token

    basket = expect_status(order_api.add_basket_item(token, burger["id"]), 201).json()
    expect_status(restaurant_api.update_item(merchant_token, burger["id"], {"price": "75.00"}), 200)

    basket = expect_status(order_api.get_basket(token, basket["id"]), 200).json()
    assert Decimal(basket["items"][0]["price"]) == Decimal("50.00")
    order = _place(order_api, customer, basket["id"])
    assert Decimal(order["total_price"]) == Decimal("50.00")
    assert Decimal(order["items"][0]["price"]) == Decimal("50.00")

    basket = expect_status(order_api.add_basket_item(token, burger["id"]), 201).json()
    assert Decimal(basket["items"][0]["price"]) == Decimal("75.00")
    expect_status(restaurant_api.update_item(merchant_token, burger["id"], {"price": "80.00"}), 200)
    basket = expect_status(order_api.add_basket_item(token, burger["id"]), 201).json()
    assert [(i["quantity"], Decimal(i["price"])) for i in basket["items"]] == [(2, Decimal("80.00"))]
    order = _place(order_api, customer, basket["id"])
    assert Decimal(order["total_price"]) == Decimal("160.00")

    basket = expect_status(order_api.add_basket_item(token, fries["id"]), 201).json()
    expect_status(restaurant_api.update_item(merchant_token, fries["id"], {"is_active": False}), 200)

    response = expect_status(order_api.add_basket_item(token, fries["id"]), 404)
    assert response.json()["detail"] == "Item not found"
    order = _place(order_api, customer, basket["id"])
    assert [(i["item_id"], Decimal(i["price"])) for i in order["items"]] == [(fries["id"], Decimal("30.00"))]

    rows = order_db.fetch_all(
        "SELECT total_price FROM orders WHERE user_id = :id ORDER BY created_at", id=customer.user_id
    )
    assert [row["total_price"] for row in rows] == [Decimal("50.00"), Decimal("160.00"), Decimal("30.00")]
