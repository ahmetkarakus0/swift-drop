import uuid
from typing import Annotated

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from core.database import get_db
from core.restaurant_service import get_restaurant_service_client
from core.user_service import get_user_service_client
from repositories.basket_repo import BasketRepository
from repositories.order_repo import OrderRepository
from schemas.auth_schema import CurrentUser, UserRole
from services.auth_service import AuthService
from services.basket_service import BasketService
from services.catalog_service import CatalogService
from services.order_service import OrderService

bearer_scheme = HTTPBearer(auto_error=False)


def get_auth_service(
    client: Annotated[httpx.Client, Depends(get_user_service_client)],
) -> AuthService:
    return AuthService(client)


def get_catalog_service(
    client: Annotated[httpx.Client, Depends(get_restaurant_service_client)],
) -> CatalogService:
    return CatalogService(client)


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


def get_current_customer_user_id(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> uuid.UUID:
    if current_user.role != UserRole.CUSTOMER:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not have permission to do this")
    return current_user.id


def get_basket_repository(db: Annotated[Session, Depends(get_db)]) -> BasketRepository:
    return BasketRepository(db)


def get_order_repository(db: Annotated[Session, Depends(get_db)]) -> OrderRepository:
    return OrderRepository(db)


def get_basket_service(
    basket_repo: Annotated[BasketRepository, Depends(get_basket_repository)],
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
) -> BasketService:
    return BasketService(basket_repo, catalog_service)


def get_order_service(
    basket_repo: Annotated[BasketRepository, Depends(get_basket_repository)],
    order_repo: Annotated[OrderRepository, Depends(get_order_repository)],
) -> OrderService:
    return OrderService(basket_repo, order_repo)
