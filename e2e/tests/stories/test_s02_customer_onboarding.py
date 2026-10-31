import pytest

from framework import data
from framework.http_client import expect_status


@pytest.mark.story
def test_customer_cannot_shop_until_email_is_verified(actors, menus, order_api, user_db, order_db):
    merchant = actors.merchant()
    menu = menus.create(merchant)

    customer = actors.customer(verified=False, login=True)
    token = customer.access_token

    response = expect_status(order_api.add_basket_item(token, menu.item["id"]), 403)
    assert response.json()["detail"] == "User is not verified"
    assert order_db.scalar("SELECT count(*) FROM baskets WHERE user_id = :id", id=customer.user_id) == 0

    actors.verify_email(customer)
    assert user_db.scalar("SELECT is_verified FROM users WHERE id = :id", id=customer.user_id) is True

    basket = expect_status(order_api.add_basket_item(token, menu.item["id"]), 201).json()
    order = expect_status(order_api.place_order(token, data.order_payload(basket["id"])), 201).json()

    assert order["status"] == "pending"
    assert order["user_id"] == customer.user_id
    assert order["restaurant_id"] == menu.restaurant_id
    row = order_db.fetch_one("SELECT user_id, status FROM orders WHERE id = :id", id=order["id"])
    assert str(row["user_id"]) == customer.user_id
    assert row["status"] == "pending"
