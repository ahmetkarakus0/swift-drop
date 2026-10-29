"""After logout neither the access nor the refresh token of that session can be used.

Logout stores both tokens in Redis as revoked until they expire. Other sessions of the
same user keep working and the user can log in again.
"""

import pytest
from redis import Redis

from framework.actors import Actor, Actors
from framework.http_client import expect_status
from framework.services import UserServiceApi

REVOKED_TOKEN_KEY_PREFIX = "user_tokens:"


def _assert_revoked(redis_client: Redis, token: str) -> None:
    key = f"{REVOKED_TOKEN_KEY_PREFIX}{token}"
    assert redis_client.exists(key) == 1, "token is not marked as revoked in Redis"
    assert redis_client.ttl(key) > 0, "revocation entry should expire together with the token"


@pytest.mark.user_service
@pytest.mark.parametrize("role", ["customer", "courier", "merchant"])
def test_logout_revokes_session_tokens(role: str, actors: Actors, user_api: UserServiceApi, redis_client: Redis):
    user: Actor = getattr(actors, role)()
    access_token, refresh_token = user.access_token, user.refresh_token
    expect_status(user_api.me(access_token), 200)

    expect_status(user_api.logout(access_token, refresh_token), 204)

    _assert_revoked(redis_client, access_token)
    _assert_revoked(redis_client, refresh_token)
    expect_status(user_api.me(access_token), 401)
    expect_status(user_api.refresh(refresh_token), 401)
    expect_status(user_api.logout(access_token, refresh_token), 401)

    actors.login(user)
    expect_status(user_api.me(user.access_token), 200)


@pytest.mark.user_service
def test_logout_does_not_affect_other_sessions(actors: Actors, user_api: UserServiceApi):
    user = actors.customer()
    first_access, first_refresh = user.access_token, user.refresh_token
    actors.login(user)

    expect_status(user_api.logout(first_access, first_refresh), 204)

    expect_status(user_api.me(first_access), 401)
    expect_status(user_api.me(user.access_token), 200)
    expect_status(user_api.refresh(user.refresh_token), 200)
