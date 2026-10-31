import pytest

from framework import data
from framework.http_client import expect_status


def _listed_ids(user_api, admin, role: str) -> dict[str, dict]:
    users = expect_status(user_api.list_users(admin.access_token, role=role, limit=100), 200).json()
    return {user["id"]: user for user in users}


@pytest.mark.story
def test_admin_approves_some_applicants_and_only_they_can_work(
    actors, user_api, courier_api, restaurant_api, user_db, courier_locations
):
    approved_courier = actors.courier(admin_verified=False)
    pending_courier = actors.courier(admin_verified=False)
    approved_merchant = actors.merchant(admin_verified=False, status=None)
    rejected_merchant = actors.merchant(admin_verified=False, status=None)
    admin = actors.admin()

    couriers = _listed_ids(user_api, admin, "courier")
    for courier in (approved_courier, pending_courier):
        assert courier.user_id in couriers, f"{courier.email} is missing from the courier list"
        assert couriers[courier.user_id]["role"] == "courier"
    merchants = _listed_ids(user_api, admin, "merchant")
    for merchant in (approved_merchant, rejected_merchant):
        assert merchant.user_id in merchants, f"{merchant.email} is missing from the merchant list"
    assert approved_courier.user_id not in merchants

    expect_status(user_api.verify_courier(approved_courier.profile_id, admin.access_token), 200)
    expect_status(user_api.verify_merchant(approved_merchant.profile_id, admin.access_token), 200)
    expect_status(user_api.set_merchant_status(approved_merchant.profile_id, "approved", admin.access_token), 200)
    expect_status(user_api.set_merchant_status(rejected_merchant.profile_id, "rejected", admin.access_token), 200)

    courier_rows = {
        str(row["id"]): row["is_verified"]
        for row in user_db.fetch_all(
            "SELECT id, is_verified FROM couriers WHERE id IN (:a, :b)",
            a=approved_courier.profile_id,
            b=pending_courier.profile_id,
        )
    }
    assert courier_rows == {approved_courier.profile_id: True, pending_courier.profile_id: False}
    merchant_rows = {
        str(row["id"]): (row["is_verified"], row["status"])
        for row in user_db.fetch_all(
            "SELECT id, is_verified, status FROM merchants WHERE id IN (:a, :b)",
            a=approved_merchant.profile_id,
            b=rejected_merchant.profile_id,
        )
    }
    assert merchant_rows == {
        approved_merchant.profile_id: (True, "approved"),
        rejected_merchant.profile_id: (False, "rejected"),
    }

    expect_status(courier_api.update_location(approved_courier.access_token, 41.0, 29.0), 204)
    assert courier_locations.position(approved_courier.profile_id) is not None

    response = expect_status(courier_api.update_location(pending_courier.access_token, 41.0, 29.0), 403)
    assert response.json()["detail"] == "Courier is not verified"
    assert courier_locations.position(pending_courier.profile_id) is None

    expect_status(restaurant_api.create_restaurant(approved_merchant.access_token, data.restaurant_payload()), 201)

    response = expect_status(
        restaurant_api.create_restaurant(rejected_merchant.access_token, data.restaurant_payload()), 403
    )
    assert response.json()["detail"] == "Merchant is not verified"
