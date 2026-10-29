from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from core.dependencies import get_auth_service, get_bearer_token, get_current_user
from models import User
from schemas.auth_schema import (
    CourierRegisterRequest,
    CourierRegisterResponse,
    CustomerRegisterRequest,
    CustomerRegisterResponse,
    LoginRequest,
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


@router.post("/login", response_model=TokenResponse)
def login(
    data: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    return auth_service.login(data)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    token: Annotated[str, Depends(get_bearer_token)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    auth_service.logout(token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserResponse)
def me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user
