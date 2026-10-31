import pytest

from framework import data
from framework.http_client import expect_status


@pytest.mark.story
def test_logged_out_tokens_are_rejected_by_every_service(actors, menus, user_api, restaurant_api, order_api):
    merchant = actors.merchant()
    menu = menus.create(merchant)
    customer = actors.customer()

    basket = expect_status(order_api.add_basket_item(customer.access_token, menu.item["id"]), 201).json()

    old_customer_token, old_merchant_token = customer.access_token, merchant.access_token
    expect_status(user_api.logout(customer.access_token, customer.refresh_token), 204)
    expect_status(user_api.logout(merchant.access_token, merchant.refresh_token), 204)

    expect_status(user_api.me(old_customer_token), 401)
    expect_status(user_api.refresh(customer.refresh_token), 401)
    expect_status(order_api.list_baskets(old_customer_token), 401)
    expect_status(order_api.place_order(old_customer_token, data.order_payload(basket["id"])), 401)
    expect_status(restaurant_api.list_orders(old_merchant_token, menu.restaurant_id), 401)

    actors.login(customer)
    actors.login(merchant)
    assert customer.access_token != old_customer_token

    baskets = expect_status(order_api.list_baskets(customer.access_token), 200).json()
    assert [b["id"] for b in baskets] == [basket["id"]]
    order = expect_status(
        order_api.place_order(customer.access_token, data.order_payload(basket["id"])), 201
    ).json()

    accepted = expect_status(
        restaurant_api.accept_order(merchant.access_token, menu.restaurant_id, order["id"]), 200
    ).json()
    assert accepted["status"] == "confirmed"
