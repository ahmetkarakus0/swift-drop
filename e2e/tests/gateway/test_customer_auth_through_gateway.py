import pytest

from framework import data
from framework.http_client import expect_status


@pytest.mark.gateway
@pytest.mark.smoke
def test_customer_registers_logs_in_and_reads_me_through_gateway(gateway_user_api, user_db):
    payload = data.customer_payload()

    registered = expect_status(gateway_user_api.register_customer(payload), 201).json()
    assert registered["email"] == payload["email"]
    assert registered["role"] == "customer"

    user_row = user_db.fetch_one("SELECT * FROM users WHERE id = :id", id=registered["id"])
    assert user_row is not None, "Registration through the gateway did not reach user-service"
    assert user_row["email"] == payload["email"]

    token = user_row["user_verification_link"]
    assert token, f"No verification token found for {payload['email']}"
    expect_status(gateway_user_api.verify_email(token), 200)

    tokens = expect_status(gateway_user_api.login(payload["email"], payload["password"]), 200).json()
    assert tokens["access_token"]
    assert tokens["token_type"] == "bearer"

    me = expect_status(gateway_user_api.me(tokens["access_token"]), 200).json()
    assert me["id"] == registered["id"]
    assert me["email"] == payload["email"]
    assert me["role"] == "customer"
    assert me["is_verified"] is True
    assert me["customer_id"] == registered["customer"]["id"]
