"""Ready-made users for case tests.

Cases usually need a user in a given state (verified customer, approved merchant,
admin...). These helpers build that state through the real APIs and only fall back
to the database for steps that have no endpoint (creating an admin, approving a courier).
"""

import uuid
from dataclasses import dataclass
from typing import Any, Optional

import bcrypt

from framework import data
from framework.config import Settings
from framework.db import Database
from framework.http_client import expect_status
from framework.services import UserServiceApi


@dataclass
class Actor:
    user_id: str
    email: str
    password: str
    role: str
    profile_id: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    registration: Optional[dict[str, Any]] = None


class Actors:
    def __init__(self, user_api: UserServiceApi, user_db: Database, settings: Settings):
        self.user_api = user_api
        self.user_db = user_db
        self.settings = settings

    def customer(self, *, verified: bool = True, login: bool = True, **overrides: Any) -> Actor:
        payload = data.customer_payload(**overrides)
        body = expect_status(self.user_api.register_customer(payload), 201).json()
        actor = self._actor(payload, body, "customer", body["customer"]["id"])
        return self._finish(actor, verified=verified, login=login)

    def courier(
        self, *, verified: bool = True, approved: bool = True, login: bool = True, **overrides: Any
    ) -> Actor:
        payload = data.courier_payload(**overrides)
        body = expect_status(self.user_api.register_courier(payload), 201).json()
        actor = self._actor(payload, body, "courier", body["courier"]["id"])
        if approved:
            self.approve_courier(actor)
        return self._finish(actor, verified=verified, login=login)

    def merchant(
        self,
        *,
        verified: bool = True,
        admin_verified: bool = True,
        status: Optional[str] = "approved",
        login: bool = True,
        **overrides: Any,
    ) -> Actor:
        payload = data.merchant_payload(**overrides)
        body = expect_status(self.user_api.register_merchant(payload), 201).json()
        actor = self._actor(payload, body, "merchant", body["merchant"]["id"])
        if admin_verified or status:
            admin = self.admin()
            if admin_verified:
                expect_status(self.user_api.verify_merchant(actor.profile_id, admin.access_token), 200)
            if status:
                expect_status(
                    self.user_api.set_merchant_status(actor.profile_id, status, admin.access_token), 200
                )
        return self._finish(actor, verified=verified, login=login)

    def admin(self, *, login: bool = True) -> Actor:
        """Admins can't register through the API, so they are inserted directly into user_db."""
        email = data.unique_email("admin")
        password = self.settings.DEFAULT_PASSWORD
        user_id = str(uuid.uuid4())
        self.user_db.execute(
            """
            INSERT INTO users (id, email, password, role, is_active, is_verified)
            VALUES (:id, :email, :password, 'admin', true, true)
            """,
            id=user_id,
            email=email,
            password=bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8"),
        )
        actor = Actor(user_id=user_id, email=email, password=password, role="admin")
        if login:
            self.login(actor)
        return actor

    def verification_token(self, actor: Actor) -> Optional[str]:
        return self.user_db.scalar(
            "SELECT user_verification_link FROM users WHERE id = :id", id=actor.user_id
        )

    def verify_email(self, actor: Actor) -> None:
        token = self.verification_token(actor)
        assert token, f"No verification token found for {actor.email}"
        expect_status(self.user_api.verify_email(token), 200)

    def approve_courier(self, actor: Actor) -> None:
        self.user_db.execute(
            "UPDATE couriers SET is_approved = true WHERE id = :id", id=actor.profile_id
        )

    def login(self, actor: Actor) -> Actor:
        tokens = expect_status(self.user_api.login(actor.email, actor.password), 200).json()
        actor.access_token = tokens["access_token"]
        actor.refresh_token = tokens["refresh_token"]
        return actor

    @staticmethod
    def _actor(payload: dict[str, Any], body: dict[str, Any], role: str, profile_id: str) -> Actor:
        return Actor(
            user_id=body["id"],
            email=payload["email"],
            password=payload["password"],
            role=role,
            profile_id=profile_id,
            registration=body,
        )

    def _finish(self, actor: Actor, *, verified: bool, login: bool) -> Actor:
        if verified:
            self.verify_email(actor)
        if login:
            self.login(actor)
        return actor
