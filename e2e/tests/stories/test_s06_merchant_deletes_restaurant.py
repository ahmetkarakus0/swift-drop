import pytest

from framework import data
from framework.http_client import expect_status


@pytest.mark.story
def test_restaurant_deleted_with_pending_order_and_full_basket(actors, menus, restaurant_api, order_api, order_db):
    """Pins current behaviour: deleting a restaurant doesn't touch order-service. The basket can still be
    ordered, and the restaurant's pending orders can no longer be listed or managed by the merchant."""
    merchant = actors.merchant()
    menu = menus.create(merchant)
    customer = actors.customer()
    token, merchant_token, item_id = customer.access_token, merchant.access_token, menu.item["id"]

    basket = expect_status(order_api.add_basket_item(token, item_id), 201).json()
    pending = expect_status(order_api.place_order(token, data.order_payload(basket["id"])), 201).json()
    basket = expect_status(order_api.add_basket_item(token, item_id), 201).json()

    expect_status(restaurant_api.delete_restaurant(merchant_token, menu.restaurant_id), 204)
    restaurants = expect_status(restaurant_api.list_restaurants(merchant_token), 200).json()
    assert menu.restaurant_id not in [r["id"] for r in restaurants]

    response = expect_status(order_api.add_basket_item(token, item_id), 404)
    assert response.json()["detail"] == "Item not found"

    late = expect_status(order_api.place_order(token, data.order_payload(basket["id"])), 201).json()
    assert late["restaurant_id"] == menu.restaurant_id
    assert late["status"] == "pending"

    response = expect_status(restaurant_api.list_orders(merchant_token, menu.restaurant_id), 404)
    assert response.json()["detail"] == "Restaurant not found"
    for order in (pending, late):
        expect_status(restaurant_api.accept_order(merchant_token, menu.restaurant_id, order["id"]), 404)
        expect_status(restaurant_api.cancel_order(merchant_token, menu.restaurant_id, order["id"]), 404)

    rows = order_db.fetch_all(
        "SELECT id, status FROM orders WHERE restaurant_id = :id", id=menu.restaurant_id
    )
    assert {str(row["id"]): row["status"] for row in rows} == {pending["id"]: "pending", late["id"]: "pending"}
