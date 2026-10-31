import pytest

from framework import data
from framework.http_client import expect_status


def _restaurant_count(restaurant_db, merchant_id: str) -> int:
    return restaurant_db.scalar("SELECT count(*) FROM restaurants WHERE merchant_id = :id", id=merchant_id)


@pytest.mark.story
def test_merchant_is_blocked_until_verified_then_opens_a_restaurant(
    actors, user_api, restaurant_api, order_api, user_db, restaurant_db
):
    merchant = actors.merchant(verified=False, admin_verified=False, status=None, login=True)
    token = merchant.access_token

    response = expect_status(restaurant_api.create_restaurant(token, data.restaurant_payload()), 403)
    assert response.json()["detail"] == "User is not verified"
    assert _restaurant_count(restaurant_db, merchant.profile_id) == 0

    actors.verify_email(merchant)
    assert user_db.scalar("SELECT is_verified FROM users WHERE id = :id", id=merchant.user_id) is True

    response = expect_status(restaurant_api.create_restaurant(token, data.restaurant_payload()), 403)
    assert response.json()["detail"] == "Merchant is not verified"
    assert _restaurant_count(restaurant_db, merchant.profile_id) == 0

    admin = actors.admin()
    expect_status(user_api.verify_merchant(merchant.profile_id, admin.access_token), 200)
    assert user_db.scalar("SELECT is_verified FROM merchants WHERE id = :id", id=merchant.profile_id) is True

    restaurant = expect_status(
        restaurant_api.create_restaurant(token, data.restaurant_payload(is_open=True)), 201
    ).json()
    assert restaurant["merchant_id"] == merchant.profile_id
    category = expect_status(
        restaurant_api.create_category(token, restaurant["id"], data.category_payload()), 201
    ).json()
    item = expect_status(restaurant_api.create_item(token, category["id"], data.item_payload()), 201).json()
    assert _restaurant_count(restaurant_db, merchant.profile_id) == 1

    customer = actors.customer()
    basket = expect_status(order_api.add_basket_item(customer.access_token, item["id"]), 201).json()
    assert basket["restaurant_id"] == restaurant["id"]
