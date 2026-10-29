"""A token is only usable while the account is eligible.

customer: users.is_active and users.is_verified
courier:  customer conditions + couriers.is_verified (admin approval)
merchant: customer conditions + merchants.is_verified (admin approval)

Login only requires an active user, so tokens are issued to ineligible accounts too; the
conditions are checked on every request. Each case keeps a single token and flips the
conditions one by one to show the same token is rejected or accepted accordingly.
"""

import pytest

from framework.actors import Actor, Actors
from framework.db import Database
from framework.http_client import expect_status
from framework.services import UserServiceApi


def _expect_forbidden(user_api: UserServiceApi, actor: Actor, detail: str) -> None:
    response = expect_status(user_api.me(actor.access_token), 403)
    assert response.json()["detail"] == detail


def _expect_allowed(user_api: UserServiceApi, actor: Actor) -> dict:
    me = expect_status(user_api.me(actor.access_token), 200).json()
    assert me["id"] == actor.user_id
    assert me["role"] == actor.role
    assert me["is_active"] is True
    assert me["is_verified"] is True
    assert me[f"{actor.role}_id"] == actor.profile_id
    return me


def _set_active(user_db: Database, actor: Actor, is_active: bool) -> None:
    user_db.execute("UPDATE users SET is_active = :value WHERE id = :id", value=is_active, id=actor.user_id)


def _assert_inactive_user_is_blocked(user_api: UserServiceApi, user_db: Database, actor: Actor) -> None:
    _set_active(user_db, actor, False)
    _expect_forbidden(user_api, actor, "User is inactive")
    expect_status(user_api.login(actor.email, actor.password), 403)

    _set_active(user_db, actor, True)
    _expect_allowed(user_api, actor)


@pytest.mark.user_service
def test_customer_requires_verified_and_active_user(actors: Actors, user_api: UserServiceApi, user_db: Database):
    customer = actors.customer(verified=False)
    _expect_forbidden(user_api, customer, "User is not verified")

    actors.verify_email(customer)
    _expect_allowed(user_api, customer)

    _assert_inactive_user_is_blocked(user_api, user_db, customer)


@pytest.mark.user_service
def test_courier_requires_user_conditions_and_admin_verification(
    actors: Actors, user_api: UserServiceApi, user_db: Database
):
    courier = actors.courier(verified=False, admin_verified=False)
    _expect_forbidden(user_api, courier, "User is not verified")

    actors.verify_email(courier)
    _expect_forbidden(user_api, courier, "Courier is not verified")

    admin = actors.admin()
    expect_status(user_api.verify_courier(courier.profile_id, admin.access_token), 200)
    assert user_db.scalar("SELECT is_verified FROM couriers WHERE id = :id", id=courier.profile_id) is True
    _expect_allowed(user_api, courier)

    _assert_inactive_user_is_blocked(user_api, user_db, courier)


@pytest.mark.user_service
def test_courier_admin_verification_does_not_replace_email_verification(actors: Actors, user_api: UserServiceApi):
    courier = actors.courier(verified=False, admin_verified=True)
    _expect_forbidden(user_api, courier, "User is not verified")

    actors.verify_email(courier)
    _expect_allowed(user_api, courier)


@pytest.mark.user_service
def test_merchant_requires_user_conditions_and_admin_verification(
    actors: Actors, user_api: UserServiceApi, user_db: Database
):
    merchant = actors.merchant(verified=False, admin_verified=False, status=None)
    _expect_forbidden(user_api, merchant, "User is not verified")

    actors.verify_email(merchant)
    _expect_forbidden(user_api, merchant, "Merchant is not verified")

    admin = actors.admin()
    expect_status(user_api.verify_merchant(merchant.profile_id, admin.access_token), 200)
    row = user_db.fetch_one("SELECT is_verified, status FROM merchants WHERE id = :id", id=merchant.profile_id)
    assert row["is_verified"] is True
    # Eligibility depends on is_verified only; the merchant is still pending.
    assert row["status"] == "pending"
    _expect_allowed(user_api, merchant)

    _assert_inactive_user_is_blocked(user_api, user_db, merchant)


@pytest.mark.user_service
def test_merchant_admin_verification_does_not_replace_email_verification(actors: Actors, user_api: UserServiceApi):
    merchant = actors.merchant(verified=False, admin_verified=True)
    _expect_forbidden(user_api, merchant, "User is not verified")

    actors.verify_email(merchant)
    _expect_allowed(user_api, merchant)
