import pytest

from framework import data
from framework.http_client import expect_status


def _restaurant_count(restaurant_db, merchant_id: str) -> int:
    return restaurant_db.scalar("SELECT count(*) FROM restaurants WHERE merchant_id = :id", id=merchant_id)


@pytest.mark.cross_service
def test_merchant_can_create_restaurant_only_after_verification(
    actors, user_api, restaurant_api, user_db, restaurant_db
):
    merchant = actors.merchant(verified=False, admin_verified=False, status=None, login=True)

    response = expect_status(
        restaurant_api.create_restaurant(merchant.access_token, data.restaurant_payload()), 403
    )
    assert response.json()["detail"] == "User is not verified"
    assert _restaurant_count(restaurant_db, merchant.profile_id) == 0

    actors.verify_email(merchant)
    assert user_db.scalar("SELECT is_verified FROM users WHERE id = :id", id=merchant.user_id) is True

    response = expect_status(
        restaurant_api.create_restaurant(merchant.access_token, data.restaurant_payload()), 403
    )
    assert response.json()["detail"] == "Merchant is not verified"
    assert _restaurant_count(restaurant_db, merchant.profile_id) == 0

    admin = actors.admin()
    expect_status(user_api.verify_merchant(merchant.profile_id, admin.access_token), 200)
    assert (
        user_db.scalar("SELECT is_verified FROM merchants WHERE id = :id", id=merchant.profile_id) is True
    )

    payload = data.restaurant_payload()
    restaurant = expect_status(restaurant_api.create_restaurant(merchant.access_token, payload), 201).json()
    assert restaurant["merchant_id"] == merchant.profile_id
    assert restaurant["name"] == payload["name"]

    row = restaurant_db.fetch_one("SELECT * FROM restaurants WHERE id = :id", id=restaurant["id"])
    assert row is not None
    assert str(row["merchant_id"]) == merchant.profile_id
    assert _restaurant_count(restaurant_db, merchant.profile_id) == 1
