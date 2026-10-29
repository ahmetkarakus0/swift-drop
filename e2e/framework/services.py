import uuid
from typing import Any

import httpx

from framework.http_client import ApiClient

Id = uuid.UUID | str | int


class UserServiceApi:
    def __init__(self, client: ApiClient):
        self.client = client

    def health(self) -> httpx.Response:
        return self.client.get("/health")

    def register_customer(self, payload: dict[str, Any]) -> httpx.Response:
        return self.client.post("/api/auth/register/customer", json=payload)

    def register_courier(self, payload: dict[str, Any]) -> httpx.Response:
        return self.client.post("/api/auth/register/courier", json=payload)

    def register_merchant(self, payload: dict[str, Any]) -> httpx.Response:
        return self.client.post("/api/auth/register/merchant", json=payload)

    def verify_email(self, token: str) -> httpx.Response:
        return self.client.get("/api/auth/verify", params={"token": token})

    def login(self, email: str, password: str) -> httpx.Response:
        return self.client.post("/api/auth/login", json={"email": email, "password": password})

    def refresh(self, refresh_token: str) -> httpx.Response:
        return self.client.post("/api/auth/refresh", json={"refresh_token": refresh_token})

    def logout(self, access_token: str, refresh_token: str) -> httpx.Response:
        return self.client.post(
            "/api/auth/logout", token=access_token, json={"refresh_token": refresh_token}
        )

    def me(self, access_token: str) -> httpx.Response:
        return self.client.get("/api/auth/me", token=access_token)

    def verify_merchant(self, merchant_id: Id, admin_token: str) -> httpx.Response:
        return self.client.post(f"/api/merchants/{merchant_id}/verify", token=admin_token)

    def set_merchant_status(self, merchant_id: Id, status: str, admin_token: str) -> httpx.Response:
        return self.client.patch(
            f"/api/merchants/{merchant_id}/status", token=admin_token, json={"status": status}
        )


class RestaurantServiceApi:
    def __init__(self, client: ApiClient):
        self.client = client

    def create_restaurant(self, token: str, payload: dict[str, Any]) -> httpx.Response:
        return self.client.post("/api/restaurants", token=token, json=payload)

    def list_restaurants(self, token: str) -> httpx.Response:
        return self.client.get("/api/restaurants", token=token)

    def get_restaurant(self, token: str, restaurant_id: Id) -> httpx.Response:
        return self.client.get(f"/api/restaurants/{restaurant_id}", token=token)

    def update_restaurant(self, token: str, restaurant_id: Id, payload: dict[str, Any]) -> httpx.Response:
        return self.client.patch(f"/api/restaurants/{restaurant_id}", token=token, json=payload)

    def delete_restaurant(self, token: str, restaurant_id: Id) -> httpx.Response:
        return self.client.delete(f"/api/restaurants/{restaurant_id}", token=token)

    def create_category(self, token: str, restaurant_id: Id, payload: dict[str, Any]) -> httpx.Response:
        return self.client.post(f"/api/restaurants/{restaurant_id}/categories", token=token, json=payload)

    def list_categories(self, token: str, restaurant_id: Id) -> httpx.Response:
        return self.client.get(f"/api/restaurants/{restaurant_id}/categories", token=token)

    def get_category(self, token: str, category_id: Id) -> httpx.Response:
        return self.client.get(f"/api/categories/{category_id}", token=token)

    def update_category(self, token: str, category_id: Id, payload: dict[str, Any]) -> httpx.Response:
        return self.client.patch(f"/api/categories/{category_id}", token=token, json=payload)

    def delete_category(self, token: str, category_id: Id) -> httpx.Response:
        return self.client.delete(f"/api/categories/{category_id}", token=token)

    def create_item(self, token: str, category_id: Id, payload: dict[str, Any]) -> httpx.Response:
        return self.client.post(f"/api/categories/{category_id}/items", token=token, json=payload)

    def list_items(self, token: str, category_id: Id) -> httpx.Response:
        return self.client.get(f"/api/categories/{category_id}/items", token=token)

    def get_item(self, token: str, item_id: Id) -> httpx.Response:
        return self.client.get(f"/api/items/{item_id}", token=token)

    def update_item(self, token: str, item_id: Id, payload: dict[str, Any]) -> httpx.Response:
        return self.client.patch(f"/api/items/{item_id}", token=token, json=payload)

    def delete_item(self, token: str, item_id: Id) -> httpx.Response:
        return self.client.delete(f"/api/items/{item_id}", token=token)
