import random

import pytest

from framework import data
from framework.http_client import expect_status

# Kilometres per degree of latitude on the sphere Redis GEO uses (radius 6372797.560856 m).
KM_PER_DEGREE_OF_LATITUDE = 111.2263
DISTANCE_TOLERANCE_KM = 0.01


def _north_of(origin: tuple[float, float], km: float) -> tuple[float, float]:
    latitude, longitude = origin
    return latitude + km / KM_PER_DEGREE_OF_LATITUDE, longitude


def _order_ready_for_pickup(order_api, restaurant_api, customer, merchant, menu) -> str:
    basket = expect_status(order_api.add_basket_item(customer.access_token, menu.item["id"]), 201).json()
    order = expect_status(
        order_api.place_order(customer.access_token, data.order_payload(basket["id"])), 201
    ).json()
    token, restaurant_id = merchant.access_token, menu.restaurant_id
    expect_status(restaurant_api.accept_order(token, restaurant_id, order["id"]), 200)
    expect_status(restaurant_api.prepare_order(token, restaurant_id, order["id"]), 200)
    expect_status(restaurant_api.mark_order_ready_for_pickup(token, restaurant_id, order["id"]), 200)
    return order["id"]


def _courier_search(dispatch_events, order_id: str, restaurant_id: str) -> dict:
    events = dispatch_events.for_order(order_id, 1)
    assert len(events) == 1, f"Expected one courier search for order {order_id}: {events}"
    event = events[0]
    assert event["event_type"] == event["header_event_type"] == "dispatch.courier_search_completed"
    assert event["data"]["order_id"] == order_id
    assert event["data"]["restaurant_id"] == restaurant_id
    return event["data"]


def _candidates(search: dict) -> list[tuple[str, float]]:
    return [(c["courier_id"], c["distance_km"]) for c in search["candidates"]]


@pytest.mark.story
def test_ready_order_searches_available_couriers_in_widening_radius(
    actors,
    menus,
    order_api,
    restaurant_api,
    courier_api,
    courier_locations,
    courier_availability,
    restaurant_locations,
    dispatch_events,
):
    # A random spot keeps couriers left over from other runs or local data out of the search.
    origin = (random.uniform(-60, 60), random.uniform(-170, 170))

    merchant = actors.merchant()
    menu = menus.create(merchant, latitude=origin[0], longitude=origin[1])
    restaurant_id = menu.restaurant_id
    assert (menu.restaurant["latitude"], menu.restaurant["longitude"]) == origin
    assert restaurant_locations.position(restaurant_id) == (
        pytest.approx(origin[0], abs=1e-4),
        pytest.approx(origin[1], abs=1e-4),
    )

    # Five couriers around the restaurant. Only those at 3 and 4 km are available at first:
    # the 0.5 km one hasn't gone online, the 1 km one is busy and the 8 km one is too far.
    distances_km = {"offline": 0.5, "busy": 1.0, "mid": 3.0, "far": 4.0, "outside": 8.0}
    couriers = {name: actors.courier() for name in distances_km}
    for name, courier in couriers.items():
        expect_status(courier_api.update_location(courier.access_token, *_north_of(origin, distances_km[name])), 204)
        assert courier_locations.position(courier.profile_id) is not None
        if name != "offline":
            expect_status(courier_api.go_online(courier.access_token), 204)
    courier_availability.mark_busy(couriers["busy"].profile_id)
    assert not courier_availability.is_online(couriers["offline"].profile_id)
    assert all(courier_availability.is_online(c.profile_id) for n, c in couriers.items() if n != "offline")

    customer = actors.customer()
    ids = {name: courier.profile_id for name, courier in couriers.items()}

    # Nobody available within 2 km, so the search widens to 5 km; nearest first.
    order_id = _order_ready_for_pickup(order_api, restaurant_api, customer, merchant, menu)
    search = _courier_search(dispatch_events, order_id, restaurant_id)
    assert search["radius_km"] == 5.0
    assert _candidates(search) == [
        (ids["mid"], pytest.approx(3.0, abs=DISTANCE_TOLERANCE_KM)),
        (ids["far"], pytest.approx(4.0, abs=DISTANCE_TOLERANCE_KM)),
    ]

    # The nearby courier comes online: the 2 km search now finds them and stops there.
    expect_status(courier_api.go_online(couriers["offline"].access_token), 204)
    assert courier_availability.is_online(ids["offline"])
    order_id = _order_ready_for_pickup(order_api, restaurant_api, customer, merchant, menu)
    search = _courier_search(dispatch_events, order_id, restaurant_id)
    assert search["radius_km"] == 2.0
    assert _candidates(search) == [(ids["offline"], pytest.approx(0.5, abs=DISTANCE_TOLERANCE_KM))]

    # They go offline again, and the next order falls back to the 5 km couriers.
    expect_status(courier_api.go_offline(couriers["offline"].access_token), 204)
    assert not courier_availability.is_online(ids["offline"])
    order_id = _order_ready_for_pickup(order_api, restaurant_api, customer, merchant, menu)
    search = _courier_search(dispatch_events, order_id, restaurant_id)
    assert search["radius_km"] == 5.0
    assert [courier_id for courier_id, _ in _candidates(search)] == [ids["mid"], ids["far"]]

    # The restaurant moves 20 km south; no courier is within 5 km of the new address.
    moved = (origin[0] - 20 / KM_PER_DEGREE_OF_LATITUDE, origin[1])
    expect_status(
        restaurant_api.update_restaurant(
            merchant.access_token, restaurant_id, {"latitude": moved[0], "longitude": moved[1]}
        ),
        200,
    )
    assert restaurant_locations.position(restaurant_id) == (
        pytest.approx(moved[0], abs=1e-4),
        pytest.approx(moved[1], abs=1e-4),
    )
    order_id = _order_ready_for_pickup(order_api, restaurant_api, customer, merchant, menu)
    search = _courier_search(dispatch_events, order_id, restaurant_id)
    assert search["radius_km"] is None
    assert search["candidates"] == []

    # Deleting the restaurant removes it from the location index.
    expect_status(restaurant_api.delete_restaurant(merchant.access_token, restaurant_id), 204)
    assert restaurant_locations.position(restaurant_id) is None
