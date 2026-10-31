import pytest

from framework.http_client import expect_status

LATITUDE = 41.0082
LONGITUDE = 28.9784


@pytest.mark.story
def test_courier_is_blocked_until_verified_then_shares_location(
    actors, user_api, courier_api, user_db, courier_locations
):
    courier = actors.courier(verified=False, admin_verified=False, login=True)
    token = courier.access_token

    response = expect_status(courier_api.update_location(token, LATITUDE, LONGITUDE), 403)
    assert response.json()["detail"] == "User is not verified"
    assert courier_locations.position(courier.profile_id) is None

    actors.verify_email(courier)
    assert user_db.scalar("SELECT is_verified FROM users WHERE id = :id", id=courier.user_id) is True

    response = expect_status(courier_api.update_location(token, LATITUDE, LONGITUDE), 403)
    assert response.json()["detail"] == "Courier is not verified"
    assert courier_locations.position(courier.profile_id) is None

    admin = actors.admin()
    expect_status(user_api.verify_courier(courier.profile_id, admin.access_token), 200)
    assert user_db.scalar("SELECT is_verified FROM couriers WHERE id = :id", id=courier.profile_id) is True

    expect_status(courier_api.update_location(token, LATITUDE, LONGITUDE), 204)

    position = courier_locations.position(courier.profile_id)
    assert position is not None, "Location of the approved courier was not stored"
    assert position == (pytest.approx(LATITUDE, abs=1e-4), pytest.approx(LONGITUDE, abs=1e-4))
