import uuid

import jwt
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from core.security import create_access_token, decode_access_token, hash_password, verify_password
from models import Address, Courier, Customer, User, UserRole
from repositories.user_repo import UserRepository
from schemas.address_schema import AddressCreate
from schemas.auth_schema import (
    BaseRegisterRequest,
    CourierRegisterRequest,
    CustomerRegisterRequest,
    LoginRequest,
    TokenResponse,
)


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def register_customer(self, data: CustomerRegisterRequest) -> User:
        user = self._build_user(data, UserRole.CUSTOMER)
        user.customer = Customer(
            first_name=data.first_name,
            last_name=data.last_name,
            phone_number=data.phone_number,
            addresses=[self._build_default_address(data.address)],
        )
        return self._save_new_user(user)

    def register_courier(self, data: CourierRegisterRequest) -> User:
        user = self._build_user(data, UserRole.COURIER)
        user.courier = Courier(
            first_name=data.first_name,
            last_name=data.last_name,
            phone_number=data.phone_number,
            vehicle_type=data.vehicle_type,
            vehicle_plate=data.vehicle_plate,
            addresses=[self._build_default_address(data.address)],
        )
        return self._save_new_user(user)

    def login(self, data: LoginRequest) -> TokenResponse:
        user = self.user_repo.get_by_email(data.email)
        if user is None or not verify_password(data.password, user.password):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
        if not user.is_active:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "User is inactive")

        token, expires_in = create_access_token(user.id, user.role)
        return TokenResponse(access_token=token, expires_in=expires_in)

    def get_user_from_token(self, token: str) -> User:
        credentials_error = HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            user_id = uuid.UUID(decode_access_token(token)["sub"])
        except (jwt.InvalidTokenError, ValueError):
            raise credentials_error

        user = self.user_repo.get_by_id(user_id)
        if user is None:
            raise credentials_error
        if not user.is_active:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "User is inactive")
        return user

    def _build_user(self, data: BaseRegisterRequest, role: UserRole) -> User:
        if self.user_repo.get_by_email(data.email):
            raise HTTPException(status.HTTP_409_CONFLICT, "Email is already registered")
        return User(email=data.email, password=hash_password(data.password), role=role)

    @staticmethod
    def _build_default_address(data: AddressCreate) -> Address:
        return Address(**data.model_dump(), is_default=True)

    def _save_new_user(self, user: User) -> User:
        try:
            return self.user_repo.create(user)
        except IntegrityError:
            self.user_repo.db.rollback()
            raise HTTPException(status.HTTP_409_CONFLICT, "Email is already registered")
