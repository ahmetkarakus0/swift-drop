from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis import Redis
from sqlalchemy.orm import Session

from core.database import engine, get_db
from core.redis import get_redis, redis_client
from models import User, UserRole
from repositories.merchant_repo import MerchantRepository
from repositories.token_repo import TokenRepository
from repositories.user_repo import UserRepository
from services.auth_service import AuthService
from services.health_service import HealthService
from services.merchant_service import MerchantService

bearer_scheme = HTTPBearer(auto_error=False)


def get_user_repository(db: Annotated[Session, Depends(get_db)]) -> UserRepository:
    return UserRepository(db)


def get_token_repository(redis: Annotated[Redis, Depends(get_redis)]) -> TokenRepository:
    return TokenRepository(redis)


def get_auth_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    token_repo: Annotated[TokenRepository, Depends(get_token_repository)],
) -> AuthService:
    return AuthService(user_repo, token_repo)


def get_bearer_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> str:
    if credentials is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


def get_authenticated_user(
    token: Annotated[str, Depends(get_bearer_token)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    """Valid token and active user only. Use for onboarding routes that pending users must reach."""
    return auth_service.get_user_from_token(token)


def get_current_user(
    user: Annotated[User, Depends(get_authenticated_user)],
) -> User:
    return AuthService.ensure_eligible(user)


def require_roles(*roles: UserRole) -> Callable[..., User]:
    """Usage: Depends(require_roles(UserRole.ADMIN))"""

    def checker(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not have permission to do this")
        return current_user

    return checker


def get_merchant_service(db: Annotated[Session, Depends(get_db)]) -> MerchantService:
    return MerchantService(MerchantRepository(db))


def get_health_service() -> HealthService:
    return HealthService(engine, redis_client)
