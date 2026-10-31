import uuid
from typing import Annotated

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis import Redis

from core.config.settings import settings
from core.redis import get_redis
from core.user_service import get_user_service_client
from repositories.location_repo import LocationRepository
from schemas.auth_schema import CurrentUser, UserRole
from services.auth_service import AuthService
from services.location_service import LocationService

bearer_scheme = HTTPBearer(auto_error=False)


def get_auth_service(
    client: Annotated[httpx.Client, Depends(get_user_service_client)],
) -> AuthService:
    return AuthService(client)


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


def get_current_user(
    token: Annotated[str, Depends(get_bearer_token)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> CurrentUser:
    return auth_service.get_current_user(token)


def get_current_courier_id(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> uuid.UUID:
    if current_user.role != UserRole.COURIER or current_user.courier_id is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not have permission to do this")
    return current_user.courier_id


def get_location_repository(redis: Annotated[Redis, Depends(get_redis)]) -> LocationRepository:
    return LocationRepository(redis, settings.COURIER_LOCATIONS_KEY)


def get_location_service(
    location_repo: Annotated[LocationRepository, Depends(get_location_repository)],
) -> LocationService:
    return LocationService(location_repo)
