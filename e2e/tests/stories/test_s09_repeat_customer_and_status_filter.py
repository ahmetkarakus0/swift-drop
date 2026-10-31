import pytest

from framework import data
from framework.http_client import expect_status


@pytest.mark.story
def test_merchant_tracks_a_repeat_customers_orders_by_status(actors, menus, restaurant_api, order_api):
    merchant = actors.merchant()
    menu = menus.create(merchant)
    customer = actors.customer()

    orders = []
    for _ in range(5):
        basket = expect_status(order_api.add_basket_item(customer.access_token, menu.item["id"]), 201).json()
        orders.append(
            expect_status(order_api.place_order(customer.access_token, data.order_payload(basket["id"])), 201).json()
        )
    ready, preparing, confirmed, cancelled, pending = (o["id"] for o in orders)

    token, restaurant_id = merchant.access_token, menu.restaurant_id
    actions = {
        ready: [restaurant_api.accept_order, restaurant_api.prepare_order, restaurant_api.mark_order_ready_for_pickup],
        preparing: [restaurant_api.accept_order, restaurant_api.prepare_order],
        confirmed: [restaurant_api.accept_order],
        cancelled: [restaurant_api.cancel_order],
    }
    for order_id, steps in actions.items():
        for step in steps:
            expect_status(step(token, restaurant_id, order_id), 200)

    everything = expect_status(restaurant_api.list_orders(token, restaurant_id), 200).json()
    assert [o["id"] for o in everything] == [pending, cancelled, confirmed, preparing, ready]

    expected = {
        "pending": [pending],
        "confirmed": [confirmed],
        "preparing": [preparing],
        "ready_for_pickup": [ready],
        "cancelled": [cancelled],
        "delivered": [],
    }
    for status, order_ids in expected.items():
        listed = expect_status(restaurant_api.list_orders(token, restaurant_id, status=status), 200).json()
        assert [o["id"] for o in listed] == order_ids, f"status={status}"
        assert all(o["status"] == status for o in listed)
