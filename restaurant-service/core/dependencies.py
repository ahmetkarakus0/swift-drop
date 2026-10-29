import uuid
from typing import Annotated

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from core.database import get_db
from core.user_service import get_user_service_client
from repositories.category_repo import CategoryRepository
from repositories.item_repo import ItemRepository
from repositories.restaurant_repo import RestaurantRepository
from schemas.auth_schema import CurrentUser, UserRole
from services.auth_service import AuthService
from services.category_service import CategoryService
from services.item_service import ItemService
from services.restaurant_service import RestaurantService

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


def get_current_merchant_id(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> uuid.UUID:
    if current_user.role != UserRole.MERCHANT or current_user.merchant_id is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not have permission to do this")
    return current_user.merchant_id


def get_restaurant_repository(db: Annotated[Session, Depends(get_db)]) -> RestaurantRepository:
    return RestaurantRepository(db)


def get_category_repository(db: Annotated[Session, Depends(get_db)]) -> CategoryRepository:
    return CategoryRepository(db)


def get_item_repository(db: Annotated[Session, Depends(get_db)]) -> ItemRepository:
    return ItemRepository(db)


def get_restaurant_service(
    restaurant_repo: Annotated[RestaurantRepository, Depends(get_restaurant_repository)],
) -> RestaurantService:
    return RestaurantService(restaurant_repo)


def get_category_service(
    restaurant_repo: Annotated[RestaurantRepository, Depends(get_restaurant_repository)],
    category_repo: Annotated[CategoryRepository, Depends(get_category_repository)],
) -> CategoryService:
    return CategoryService(restaurant_repo, category_repo)


def get_item_service(
    category_repo: Annotated[CategoryRepository, Depends(get_category_repository)],
    item_repo: Annotated[ItemRepository, Depends(get_item_repository)],
) -> ItemService:
    return ItemService(category_repo, item_repo)
