from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from core.dependencies import get_auth_service, get_bearer_token, get_current_user
from models import User
from schemas.auth_schema import (
    CourierRegisterRequest,
    CourierRegisterResponse,
    CustomerRegisterRequest,
    CustomerRegisterResponse,
    LoginRequest,
    LogoutRequest,
    MerchantRegisterRequest,
    MerchantRegisterResponse,
    RefreshRequest,
    TokenResponse,
)
from schemas.user_schema import UserResponse
from services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register/customer",
    response_model=CustomerRegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_customer(
    data: CustomerRegisterRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    return auth_service.register_customer(data)


@router.post(
    "/register/courier",
    response_model=CourierRegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_courier(
    data: CourierRegisterRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    return auth_service.register_courier(data)


@router.post(
    "/register/merchant",
    response_model=MerchantRegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_merchant(
    data: MerchantRegisterRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    return auth_service.register_merchant(data)


@router.post("/login", response_model=TokenResponse)
def login(
    data: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    return auth_service.login(data)


@router.get("/verify", response_model=UserResponse)
def verify_user(
    token: Annotated[str, Query(min_length=1, max_length=64)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    return auth_service.verify_user(token)


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    data: RefreshRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    return auth_service.refresh(data.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    data: LogoutRequest,
    token: Annotated[str, Depends(get_bearer_token)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    auth_service.logout(token, data.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserResponse)
def me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user
