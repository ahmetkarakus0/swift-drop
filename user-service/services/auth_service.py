import logging
import math
import time
import uuid

import jwt
from fastapi import HTTPException, status
from redis.exceptions import RedisError
from sqlalchemy.exc import IntegrityError

from core.security import (
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from models import Address, Courier, Customer, Merchant, User, UserRole
from repositories.token_repo import TokenRepository
from repositories.user_repo import UserRepository
from schemas.address_schema import AddressCreate
from schemas.auth_schema import (
    BaseRegisterRequest,
    CourierRegisterRequest,
    CustomerRegisterRequest,
    LoginRequest,
    MerchantRegisterRequest,
    TokenResponse,
)

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, user_repo: UserRepository, token_repo: TokenRepository):
        self.user_repo = user_repo
        self.token_repo = token_repo

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

    def register_merchant(self, data: MerchantRegisterRequest) -> User:
        user = self._build_user(data, UserRole.MERCHANT)
        user.merchant = Merchant(
            business_name=data.business_name,
            phone_number=data.phone_number,
            tax_number=data.tax_number,
            tax_office=data.tax_office,
            iban=data.iban,
            addresses=[self._build_default_address(data.address)],
        )
        return self._save_new_user(user)

    def login(self, data: LoginRequest) -> TokenResponse:
        user = self.user_repo.get_by_email(data.email)
        if user is None or not verify_password(data.password, user.password):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
        if not user.is_active:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "User is inactive")

        return self._issue_tokens(user)

    def refresh(self, refresh_token: str) -> TokenResponse:
        payload = self._decode_valid_token(refresh_token, TokenType.REFRESH)
        user = self._get_active_user(payload)
        # Rotation: consuming the token atomically makes it single-use, even under concurrent requests.
        if not self._revoke(refresh_token, payload):
            raise self._credentials_error()
        return self._issue_tokens(user)

    def logout(self, access_token: str, refresh_token: str) -> None:
        access_payload = self._decode_valid_token(access_token, TokenType.ACCESS)
        self._revoke(access_token, access_payload)

        try:
            refresh_payload = decode_token(refresh_token, TokenType.REFRESH)
        except jwt.InvalidTokenError:
            # An expired or invalid refresh token can't be used anyway.
            return
        if refresh_payload["sub"] == access_payload["sub"]:
            self._revoke(refresh_token, refresh_payload)

    def get_user_from_token(self, token: str) -> User:
        payload = self._decode_valid_token(token, TokenType.ACCESS)
        return self._get_active_user(payload)

    @staticmethod
    def _issue_tokens(user: User) -> TokenResponse:
        access_token, expires_in = create_access_token(user.id, user.role)
        refresh_token, refresh_expires_in = create_refresh_token(user.id)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            refresh_expires_in=refresh_expires_in,
        )

    def _get_active_user(self, payload: dict) -> User:
        try:
            user_id = uuid.UUID(payload["sub"])
        except ValueError:
            raise self._credentials_error()

        user = self.user_repo.get_by_id(user_id)
        if user is None:
            raise self._credentials_error()
        if not user.is_active:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "User is inactive")
        return user

    def _decode_valid_token(self, token: str, expected_type: TokenType) -> dict:
        try:
            payload = decode_token(token, expected_type)
        except jwt.InvalidTokenError:
            raise self._credentials_error()

        try:
            revoked = self.token_repo.is_revoked(token)
        except RedisError:
            # Fail closed: without Redis we cannot tell whether the token was logged out.
            logger.exception("Could not check token revocation")
            raise self._auth_unavailable_error()
        if revoked:
            raise self._credentials_error()
        return payload

    def _revoke(self, token: str, payload: dict) -> bool:
        """Returns False if the token was already revoked."""
        ttl_seconds = math.ceil(payload["exp"] - time.time())
        if ttl_seconds <= 0:
            return True
        try:
            return self.token_repo.revoke(token, ttl_seconds)
        except RedisError:
            logger.exception("Could not revoke token")
            raise self._auth_unavailable_error()

    @staticmethod
    def _credentials_error() -> HTTPException:
        return HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    @staticmethod
    def _auth_unavailable_error() -> HTTPException:
        return HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "Authentication is temporarily unavailable"
        )

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
