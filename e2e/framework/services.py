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

    def list_users(
        self, admin_token: str, role: str | None = None, limit: int = 50, offset: int = 0
    ) -> httpx.Response:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if role is not None:
            params["role"] = role
        return self.client.get("/api/users", token=admin_token, params=params)

    def verify_courier(self, courier_id: Id, admin_token: str) -> httpx.Response:
        return self.client.post(f"/api/couriers/{courier_id}/verify", token=admin_token)

    def verify_merchant(self, merchant_id: Id, admin_token: str) -> httpx.Response:
        return self.client.post(f"/api/merchants/{merchant_id}/verify", token=admin_token)

    def set_merchant_status(self, merchant_id: Id, status: str, admin_token: str) -> httpx.Response:
        return self.client.patch(
            f"/api/merchants/{merchant_id}/status", token=admin_token, json={"status": status}
        )


class CourierServiceApi:
    def __init__(self, client: ApiClient):
        self.client = client

    def update_location(self, token: str, latitude: float, longitude: float) -> httpx.Response:
        return self.client.put(
            "/api/couriers/location", token=token, json={"latitude": latitude, "longitude": longitude}
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

    def list_orders(self, token: str, restaurant_id: Id, status: str | None = None) -> httpx.Response:
        params = {"status": status} if status is not None else None
        return self.client.get(f"/api/restaurants/{restaurant_id}/orders", token=token, params=params)

    def accept_order(self, token: str, restaurant_id: Id, order_id: Id) -> httpx.Response:
        return self._order_action(token, restaurant_id, order_id, "accept")

    def prepare_order(self, token: str, restaurant_id: Id, order_id: Id) -> httpx.Response:
        return self._order_action(token, restaurant_id, order_id, "prepare")

    def mark_order_ready_for_pickup(self, token: str, restaurant_id: Id, order_id: Id) -> httpx.Response:
        return self._order_action(token, restaurant_id, order_id, "ready-for-pickup")

    def cancel_order(self, token: str, restaurant_id: Id, order_id: Id) -> httpx.Response:
        return self._order_action(token, restaurant_id, order_id, "cancel")

    def _order_action(self, token: str, restaurant_id: Id, order_id: Id, action: str) -> httpx.Response:
        return self.client.put(f"/api/restaurants/{restaurant_id}/orders/{order_id}/{action}", token=token)


class OrderServiceApi:
    def __init__(self, client: ApiClient):
        self.client = client

    def add_basket_item(self, token: str, item_id: Id, quantity: int = 1) -> httpx.Response:
        return self.client.post("/api/baskets/items", token=token, json={"item_id": item_id, "quantity": quantity})

    def list_baskets(self, token: str) -> httpx.Response:
        return self.client.get("/api/baskets", token=token)

    def get_basket(self, token: str, basket_id: Id) -> httpx.Response:
        return self.client.get(f"/api/baskets/{basket_id}", token=token)

    def update_basket_item(self, token: str, basket_id: Id, basket_item_id: Id, quantity: int) -> httpx.Response:
        return self.client.patch(
            f"/api/baskets/{basket_id}/items/{basket_item_id}", token=token, json={"quantity": quantity}
        )

    def remove_basket_item(self, token: str, basket_id: Id, basket_item_id: Id) -> httpx.Response:
        return self.client.delete(f"/api/baskets/{basket_id}/items/{basket_item_id}", token=token)

    def place_order(self, token: str, payload: dict[str, Any]) -> httpx.Response:
        return self.client.post("/api/orders", token=token, json=payload)
