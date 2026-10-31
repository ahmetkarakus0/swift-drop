import pytest

from framework import data
from framework.http_client import expect_status

LATITUDE = 40.9903
LONGITUDE = 29.0290


@pytest.mark.story
@pytest.mark.gateway
@pytest.mark.smoke
def test_order_reaches_ready_for_pickup_with_a_courier_online_through_gateway(
    gateway_actors, gateway_menus, gateway_restaurant_api, gateway_order_api, gateway_courier_api,
    order_db, courier_locations,
):
    merchant = gateway_actors.merchant()
    customer = gateway_actors.customer()
    courier = gateway_actors.courier()
    menu = gateway_menus.create(merchant)

    expect_status(gateway_courier_api.update_location(courier.access_token, LATITUDE, LONGITUDE), 204)
    assert courier_locations.position(courier.profile_id) == (
        pytest.approx(LATITUDE, abs=1e-4),
        pytest.approx(LONGITUDE, abs=1e-4),
    )

    basket = expect_status(gateway_order_api.add_basket_item(customer.access_token, menu.item["id"], 2), 201).json()
    order = expect_status(
        gateway_order_api.place_order(customer.access_token, data.order_payload(basket["id"])), 201
    ).json()
    assert order["status"] == "pending"

    token, restaurant_id = merchant.access_token, menu.restaurant_id
    incoming = expect_status(gateway_restaurant_api.list_orders(token, restaurant_id, status="pending"), 200).json()
    assert [o["id"] for o in incoming] == [order["id"]]

    for action, expected in (
        (gateway_restaurant_api.accept_order, "confirmed"),
        (gateway_restaurant_api.prepare_order, "preparing"),
        (gateway_restaurant_api.mark_order_ready_for_pickup, "ready_for_pickup"),
    ):
        assert expect_status(action(token, restaurant_id, order["id"]), 200).json()["status"] == expected

    row = order_db.fetch_one("SELECT status, courier_id FROM orders WHERE id = :id", id=order["id"])
    assert row == {"status": "ready_for_pickup", "courier_id": None}
