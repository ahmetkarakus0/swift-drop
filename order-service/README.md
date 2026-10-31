# Order Service

Swift Drop's order service. Lets customers fill baskets and place orders from them. It owns the `order_db` PostgreSQL database.

## Tech Stack

- FastAPI
- SQLAlchemy 2 + PostgreSQL (psycopg 3)
- Alembic for migrations
- httpx for calling the user service and the restaurant service

## Project Structure

```
core/           settings, database session, user/restaurant service clients, shared dependencies
models/         SQLAlchemy models (baskets, basket items, orders, order items)
schemas/        Pydantic request/response models
repositories/   database access
services/       business logic
routes/         API endpoints
alembic/        database migrations
```

## Setup

1. Start PostgreSQL from the repository root:

   ```bash
   docker compose up -d
   ```

2. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and fill in the values. `USER_SERVICE_URL` and `RESTAURANT_SERVICE_URL` must point to running services.

4. Apply migrations and start the service:

   ```bash
   alembic upgrade head
   python main.py
   ```

API docs are available at http://127.0.0.1:8002/docs.

## Authentication

Every `/api` endpoint requires `Authorization: Bearer <access_token>`, using an access token issued by the user service. The token is checked by calling the user service's `GET /api/auth/me`, so the user service must be running.

Only customers can use this service; other roles get `403`. If the user service can't be reached, requests fail with `503`.

Customers can only see and change their own baskets; anything else returns `404`.

## Baskets

A customer has one basket per restaurant. When an item is added, its name, price and restaurant are fetched from the restaurant service's `GET /internal/items/{item_id}`; the client only sends the item ID and quantity. The basket for that restaurant is created if it doesn't exist yet.

- Adding an item that is already in the basket increases its quantity (up to 99) and refreshes its name and price.
- Inactive items, or items in an inactive category or restaurant, return `404`. Items from a closed restaurant return `409`.
- Removing the last item deletes the basket.
- If the restaurant service can't be reached, adding items fails with `503`.

## Orders

An order is placed from a basket. The basket's items are copied into the order with the prices saved in the basket, the total is calculated, the status starts as `pending`, and the basket is deleted. An empty basket returns `400`.

## Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/api/baskets/items` | Add an item to the basket of its restaurant. Body: `{"item_id": 12, "quantity": 2}` (`quantity` defaults to 1, max 99) |
| GET | `/api/baskets` | List the customer's baskets |
| GET | `/api/baskets/{basket_id}` | Get a basket with its items and total price |
| PATCH | `/api/baskets/{basket_id}/items/{basket_item_id}` | Change an item's quantity. Body: `{"quantity": 3}` |
| DELETE | `/api/baskets/{basket_id}/items/{basket_item_id}` | Remove an item from the basket |
| DELETE | `/api/baskets/{basket_id}` | Delete a basket |
| POST | `/api/orders` | Place an order from a basket. Body: `{"basket_id": "...", "delivery_address": "..."}` |

## Internal Endpoints

These are for other services and are mounted outside `/api`, so the gateway never forwards them. They require no authentication.

| Method | Path | Description |
|---|---|---|
| GET | `/internal/restaurants/{restaurant_id}/orders` | List a restaurant's orders with their items, newest first. Optional `?status=` filter. Used by the restaurant service |
| PUT | `/internal/restaurants/{restaurant_id}/orders/{order_id}/accept` | Change a restaurant's order from `pending` to `confirmed`. Returns `404` if the order doesn't belong to the restaurant and `409` if it isn't pending. Used by the restaurant service |

## Tables

### baskets
- id: uuid, primary key
- user_id: uuid (no foreign key, users exist in another service)
- restaurant_id: uuid (no foreign key, restaurants exist in another service)
- created_at: timestamp
- updated_at: timestamp

### basket_items
- id: uuid, primary key
- basket_id: uuid, foreign key to baskets.id
- item_id: integer (no foreign key, items exist in another service)
- item_name: string
- quantity: integer
- price: decimal
- created_at: timestamp
- updated_at: timestamp

### orders
- id: uuid, primary key
- user_id: uuid (no foreign key, users exist in another service)
- restaurant_id: uuid (no foreign key, restaurants exist in another service)
- courier_id: uuid | null (no foreign key, couriers exist in another service)
- status: enum (pending, confirmed, preparing, ready_for_pickup, on_the_way, delivered, cancelled)
- total_price: decimal
- delivery_address: string
- created_at: timestamp
- updated_at: timestamp

### order_items
- id: uuid, primary key
- order_id: uuid, foreign key to orders.id
- item_id: integer (no foreign key, items exist in another service)
- item_name: string
- quantity: integer
- price: decimal
