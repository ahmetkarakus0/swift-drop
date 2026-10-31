import pytest

from framework import data
from framework.http_client import expect_status


@pytest.mark.story
def test_every_order_step_publishes_an_event_in_order(actors, menus, restaurant_api, order_api, order_events):
    merchant = actors.merchant()
    menu = menus.create(merchant)
    customer = actors.customer()

    basket = expect_status(order_api.add_basket_item(customer.access_token, menu.item["id"], 2), 201).json()
    order = expect_status(order_api.place_order(customer.access_token, data.order_payload(basket["id"])), 201).json()

    token, restaurant_id = merchant.access_token, menu.restaurant_id
    expect_status(restaurant_api.accept_order(token, restaurant_id, order["id"]), 200)
    expect_status(restaurant_api.prepare_order(token, restaurant_id, order["id"]), 200)
    expect_status(restaurant_api.mark_order_ready_for_pickup(token, restaurant_id, order["id"]), 200)

    events = order_events.for_order(order["id"], 4)
    assert len(events) == 4, f"Unexpected extra events for order {order['id']}: {events}"
    assert [e["event_type"] for e in events] == ["order.created"] + ["order.status_updated"] * 3
    assert all(e["header_event_type"] == e["event_type"] for e in events)
    assert len({e["event_id"] for e in events}) == 4

    created = events[0]["data"]
    assert created["id"] == order["id"]
    assert created["status"] == "pending"
    assert created["user_id"] == customer.user_id
    assert created["restaurant_id"] == restaurant_id
    assert created["total_price"] == order["total_price"]
    assert [(i["item_id"], i["quantity"]) for i in created["items"]] == [(menu.item["id"], 2)]

    changes = [e["data"] for e in events[1:]]
    assert [(c["previous_status"], c["status"]) for c in changes] == [
        ("pending", "confirmed"),
        ("confirmed", "preparing"),
        ("preparing", "ready_for_pickup"),
    ]
    for change in changes:
        assert change["order_id"] == order["id"]
        assert change["user_id"] == customer.user_id
        assert change["restaurant_id"] == restaurant_id
        assert change["courier_id"] is None
