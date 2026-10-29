"""A merchant's token is rejected by restaurant-service after logout.

restaurant-service validates tokens through user-service, so revoking the token in
user-service immediately blocks reads and writes there as well.
"""

import pytest

from framework import data
from framework.actors import Actors
from framework.db import Database
from framework.http_client import expect_status
from framework.services import RestaurantServiceApi, UserServiceApi


@pytest.mark.cross_service
def test_logout_blocks_restaurant_access(
    actors: Actors,
    user_api: UserServiceApi,
    restaurant_api: RestaurantServiceApi,
    restaurant_db: Database,
):
    merchant = actors.merchant()
    token = merchant.access_token
    restaurant = expect_status(restaurant_api.create_restaurant(token, data.restaurant_payload()), 201).json()

    expect_status(user_api.logout(token, merchant.refresh_token), 204)

    requests = {
        "list restaurants": restaurant_api.list_restaurants(token),
        "get restaurant": restaurant_api.get_restaurant(token, restaurant["id"]),
        "create restaurant": restaurant_api.create_restaurant(token, data.restaurant_payload()),
        "update restaurant": restaurant_api.update_restaurant(
            token, restaurant["id"], {"name": data.unique_name("After Logout")}
        ),
        "delete restaurant": restaurant_api.delete_restaurant(token, restaurant["id"]),
    }
    for name, response in requests.items():
        assert response.status_code == 401, f"{name}: {response.status_code} {response.text}"

    rows = restaurant_db.fetch_all(
        "SELECT id, name, is_active FROM restaurants WHERE merchant_id = :id", id=merchant.profile_id
    )
    assert len(rows) == 1
    assert str(rows[0]["id"]) == restaurant["id"]
    assert rows[0]["name"] == restaurant["name"]
    assert rows[0]["is_active"] is True

    actors.login(merchant)
    restaurants = expect_status(restaurant_api.list_restaurants(merchant.access_token), 200).json()
    assert [r["id"] for r in restaurants] == [restaurant["id"]]
