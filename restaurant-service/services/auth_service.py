import logging

import httpx
from fastapi import HTTPException, status

from schemas.auth_schema import CurrentUser

logger = logging.getLogger(__name__)

ME_PATH = "/api/auth/me"


class AuthService:
    """Authenticates requests by delegating token validation to user-service."""

    def __init__(self, client: httpx.Client):
        self.client = client

    def get_current_user(self, token: str) -> CurrentUser:
        try:
            response = self.client.get(ME_PATH, headers={"Authorization": f"Bearer {token}"})
        except httpx.HTTPError:
            logger.exception("Could not reach user-service")
            raise self._auth_unavailable_error()

        if response.status_code == status.HTTP_401_UNAUTHORIZED:
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED,
                self._detail(response, "Invalid or expired token"),
                headers={"WWW-Authenticate": "Bearer"},
            )
        if response.status_code == status.HTTP_403_FORBIDDEN:
            raise HTTPException(status.HTTP_403_FORBIDDEN, self._detail(response, "Forbidden"))
        if response.is_error:
            logger.error("user-service returned %s for %s", response.status_code, ME_PATH)
            raise self._auth_unavailable_error()

        try:
            return CurrentUser.model_validate(response.json())
        except ValueError:
            logger.exception("Unexpected response from user-service %s", ME_PATH)
            raise self._auth_unavailable_error()

    @staticmethod
    def _detail(response: httpx.Response, fallback: str) -> str:
        try:
            detail = response.json().get("detail")
        except (ValueError, AttributeError):
            return fallback
        return detail if isinstance(detail, str) else fallback

    @staticmethod
    def _auth_unavailable_error() -> HTTPException:
        return HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "Authentication is temporarily unavailable"
        )
