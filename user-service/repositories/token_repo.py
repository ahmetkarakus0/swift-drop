from redis import Redis

# Shared contract: other services check this key to reject logged-out tokens.
REVOKED_TOKEN_KEY_PREFIX = "user_tokens:"


class TokenRepository:
    def __init__(self, redis: Redis):
        self.redis = redis

    def revoke(self, token: str, ttl_seconds: int) -> None:
        self.redis.set(self._key(token), "revoked", ex=ttl_seconds)

    def is_revoked(self, token: str) -> bool:
        return self.redis.exists(self._key(token)) == 1

    @staticmethod
    def _key(token: str) -> str:
        return f"{REVOKED_TOKEN_KEY_PREFIX}{token}"
