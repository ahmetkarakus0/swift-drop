import pytest

from framework import data
from framework.http_client import expect_status


def _order_status(order_db, order_id: str) -> str:
    return order_db.scalar("SELECT status FROM orders WHERE id = :id", id=order_id)


@pytest.mark.story
def test_deactivated_merchant_cannot_manage_orders_until_reactivated(
    actors, menus, user_api, restaurant_api, order_api, order_db
):
    """Pins current behaviour: deactivating a merchant doesn't close their restaurant, so customers can
    keep ordering while nobody can accept the orders."""
    merchant = actors.merchant()
    menu = menus.create(merchant)
    customer = actors.customer()
    token, restaurant_id = merchant.access_token, menu.restaurant_id

    basket = expect_status(order_api.add_basket_item(customer.access_token, menu.item["id"]), 201).json()
    order = expect_status(order_api.place_order(customer.access_token, data.order_payload(basket["id"])), 201).json()
    expect_status(restaurant_api.accept_order(token, restaurant_id, order["id"]), 200)

    actors.set_active(merchant, False)

    response = expect_status(restaurant_api.prepare_order(token, restaurant_id, order["id"]), 403)
    assert response.json()["detail"] == "User is inactive"
    expect_status(restaurant_api.list_orders(token, restaurant_id), 403)
    response = expect_status(user_api.login(merchant.email, merchant.password), 403)
    assert response.json()["detail"] == "User is inactive"
    assert _order_status(order_db, order["id"]) == "confirmed"

    basket = expect_status(order_api.add_basket_item(customer.access_token, menu.item["id"]), 201).json()
    waiting = expect_status(
        order_api.place_order(customer.access_token, data.order_payload(basket["id"])), 201
    ).json()
    assert waiting["status"] == "pending"

    actors.set_active(merchant, True)

    prepared = expect_status(restaurant_api.prepare_order(token, restaurant_id, order["id"]), 200).json()
    assert prepared["status"] == "preparing"
    accepted = expect_status(restaurant_api.accept_order(token, restaurant_id, waiting["id"]), 200).json()
    assert accepted["status"] == "confirmed"
    assert _order_status(order_db, order["id"]) == "preparing"
    assert _order_status(order_db, waiting["id"]) == "confirmed"
