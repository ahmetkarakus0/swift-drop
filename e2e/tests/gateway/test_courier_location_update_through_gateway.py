import pytest

from framework import data
from framework.http_client import expect_status

LATITUDE = 40.9876
LONGITUDE = 29.0254


@pytest.mark.gateway
@pytest.mark.cross_service
def test_verified_courier_updates_location_through_gateway(
    gateway_user_api, gateway_courier_api, actors, user_db, redis_client, settings
):
    payload = data.courier_payload()
    registered = expect_status(gateway_user_api.register_courier(payload), 201).json()
    assert registered["role"] == "courier"
    courier_id = registered["courier"]["id"]

    token = user_db.scalar("SELECT user_verification_link FROM users WHERE id = :id", id=registered["id"])
    assert token, f"No verification token found for {payload['email']}"
    expect_status(gateway_user_api.verify_email(token), 200)
    assert user_db.scalar("SELECT is_verified FROM users WHERE id = :id", id=registered["id"]) is True

    admin = actors.admin()
    expect_status(gateway_user_api.verify_courier(courier_id, admin.access_token), 200)
    assert user_db.scalar("SELECT is_verified FROM couriers WHERE id = :id", id=courier_id) is True

    tokens = expect_status(gateway_user_api.login(payload["email"], payload["password"]), 200).json()

    member = f"courier-id-{courier_id}"
    try:
        expect_status(
            gateway_courier_api.update_location(tokens["access_token"], LATITUDE, LONGITUDE), 204
        )

        position = redis_client.geopos(settings.COURIER_LOCATIONS_KEY, member)[0]
        assert position is not None, f"{member} was not added to {settings.COURIER_LOCATIONS_KEY}"
        longitude, latitude = position
        assert longitude == pytest.approx(LONGITUDE, abs=1e-4)
        assert latitude == pytest.approx(LATITUDE, abs=1e-4)
    finally:
        if not settings.KEEP_TEST_DATA:
            redis_client.zrem(settings.COURIER_LOCATIONS_KEY, member)
