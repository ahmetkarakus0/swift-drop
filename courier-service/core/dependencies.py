import uuid
from typing import Annotated

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis import Redis

from core.config.settings import settings
from core.order_service import get_order_service_client
from core.redis import get_redis
from core.user_service import get_user_service_client
from repositories.availability_repo import AvailabilityRepository
from repositories.location_repo import LocationRepository
from repositories.restaurant_location_repo import RestaurantLocationRepository
from schemas.auth_schema import CurrentUser, UserRole
from services.auth_service import AuthService
from services.availability_service import AvailabilityService
from services.location_service import LocationService
from services.nearby_order_service import NearbyOrderService
from services.order_service import OrderService

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


def get_availability_repository(
    redis: Annotated[Redis, Depends(get_redis)],
) -> AvailabilityRepository:
    return AvailabilityRepository(redis, settings.COURIER_ONLINE_KEY)


def get_availability_service(
    availability_repo: Annotated[AvailabilityRepository, Depends(get_availability_repository)],
) -> AvailabilityService:
    return AvailabilityService(availability_repo)


def get_restaurant_location_repository(
    redis: Annotated[Redis, Depends(get_redis)],
) -> RestaurantLocationRepository:
    return RestaurantLocationRepository(redis, settings.RESTAURANT_LOCATIONS_KEY)


def get_order_service(
    client: Annotated[httpx.Client, Depends(get_order_service_client)],
) -> OrderService:
    return OrderService(client)


def get_nearby_order_service(
    location_repo: Annotated[LocationRepository, Depends(get_location_repository)],
    restaurant_location_repo: Annotated[
        RestaurantLocationRepository, Depends(get_restaurant_location_repository)
    ],
    order_service: Annotated[OrderService, Depends(get_order_service)],
) -> NearbyOrderService:
    return NearbyOrderService(location_repo, restaurant_location_repo, order_service)
