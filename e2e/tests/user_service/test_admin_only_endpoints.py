"""Courier verification and merchant verification/status endpoints are admin-only.

Fully eligible customers, couriers and merchants get 403 and the target records stay
unchanged; requests without a token get 401; an admin can perform every action.
"""

from dataclasses import dataclass

import pytest

from framework.actors import Actor, Actors
from framework.db import Database
from framework.http_client import expect_status
from framework.services import UserServiceApi


@dataclass
class Targets:
    courier: Actor
    merchant: Actor


@pytest.fixture
def targets(actors: Actors) -> Targets:
    """A courier and a merchant still waiting for admin actions."""
    return Targets(
        courier=actors.courier(admin_verified=False, login=False),
        merchant=actors.merchant(admin_verified=False, status=None, login=False),
    )


def _admin_requests(user_api: UserServiceApi, targets: Targets, token: str | None) -> dict:
    return {
        "verify courier": user_api.verify_courier(targets.courier.profile_id, token),
        "verify merchant": user_api.verify_merchant(targets.merchant.profile_id, token),
        "set merchant status": user_api.set_merchant_status(targets.merchant.profile_id, "approved", token),
    }


def _courier_row(user_db: Database, targets: Targets) -> dict:
    return user_db.fetch_one("SELECT is_verified FROM couriers WHERE id = :id", id=targets.courier.profile_id)


def _merchant_row(user_db: Database, targets: Targets) -> dict:
    return user_db.fetch_one(
        "SELECT is_verified, status FROM merchants WHERE id = :id", id=targets.merchant.profile_id
    )


def _assert_targets_unchanged(user_db: Database, targets: Targets) -> None:
    assert _courier_row(user_db, targets) == {"is_verified": False}
    assert _merchant_row(user_db, targets) == {"is_verified": False, "status": "pending"}


@pytest.mark.user_service
@pytest.mark.parametrize("role", ["customer", "courier", "merchant"])
def test_non_admin_users_are_forbidden(
    role: str, actors: Actors, targets: Targets, user_api: UserServiceApi, user_db: Database
):
    caller = getattr(actors, role)()
    expect_status(user_api.me(caller.access_token), 200)

    for name, response in _admin_requests(user_api, targets, caller.access_token).items():
        assert response.status_code == 403, f"{role} -> {name}: {response.status_code} {response.text}"
        assert response.json()["detail"] == "You do not have permission to do this"

    _assert_targets_unchanged(user_db, targets)


@pytest.mark.user_service
def test_requests_without_token_are_unauthorized(targets: Targets, user_api: UserServiceApi, user_db: Database):
    for name, response in _admin_requests(user_api, targets, None).items():
        assert response.status_code == 401, f"{name}: {response.status_code} {response.text}"

    _assert_targets_unchanged(user_db, targets)


@pytest.mark.user_service
def test_admin_can_verify_and_set_status(
    actors: Actors, targets: Targets, user_api: UserServiceApi, user_db: Database
):
    admin = actors.admin()

    for name, response in _admin_requests(user_api, targets, admin.access_token).items():
        assert response.status_code == 200, f"{name}: {response.status_code} {response.text}"

    assert _courier_row(user_db, targets) == {"is_verified": True}
    assert _merchant_row(user_db, targets) == {"is_verified": True, "status": "approved"}
