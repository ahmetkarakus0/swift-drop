import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum

import bcrypt
import jwt

from core.config.settings import settings
from models import UserRole

# bcrypt only uses the first 72 bytes and bcrypt>=5 raises for longer input.
BCRYPT_MAX_BYTES = 72


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > BCRYPT_MAX_BYTES:
        return False
    return bcrypt.checkpw(password_bytes, password_hash.encode("utf-8"))


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


def create_access_token(user_id: uuid.UUID, role: UserRole) -> tuple[str, int]:
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    return _create_token(user_id, TokenType.ACCESS, expires_in, {"role": role.value}), expires_in


def create_refresh_token(user_id: uuid.UUID) -> tuple[str, int]:
    expires_in = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    return _create_token(user_id, TokenType.REFRESH, expires_in), expires_in


def decode_token(token: str, expected_type: TokenType) -> dict:
    """Raises jwt.InvalidTokenError if the token is invalid, expired or of the wrong type."""
    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        options={"require": ["sub", "exp", "jti", "type"]},
    )
    if payload["type"] != expected_type.value:
        raise jwt.InvalidTokenError("Unexpected token type")
    return payload


def _create_token(
    user_id: uuid.UUID, token_type: TokenType, expires_in: int, extra_claims: dict | None = None
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "jti": uuid.uuid4().hex,
        "type": token_type.value,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
        **(extra_claims or {}),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
