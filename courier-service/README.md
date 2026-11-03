# Courier Service

Swift Drop's courier service. It owns the `courier_db` PostgreSQL database.

## Tech Stack

- FastAPI
- SQLAlchemy 2 + PostgreSQL (psycopg 3)
- Alembic for migrations
- Redis for courier locations and availability
- httpx for calling the user service and the order service

## Project Structure

```
core/           settings, database session, Redis client, user/order service clients, shared dependencies
models/         SQLAlchemy models
schemas/        Pydantic request/response models
repositories/   database access
services/       business logic
routes/         API endpoints
alembic/        database migrations
```

## Setup

1. Start PostgreSQL and Redis from the repository root:

   ```bash
   docker compose up -d
   ```

2. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and fill in the values. `REDIS_URL` uses the Redis from `docker-compose.yml` (password `REDIS_PASSWORD`). `USER_SERVICE_URL` must point to a running user service, and `ORDER_SERVICE_URL` to a running order service for listing nearby orders.

4. Apply migrations and start the service:

   ```bash
   alembic upgrade head
   python main.py
   ```

API docs are available at http://127.0.0.1:8003/docs.

## Authentication

Every `/api` endpoint requires `Authorization: Bearer <access_token>`, using an access token issued by the user service. The token is checked by calling the user service's `GET /api/auth/me`, so the user service must be running.

Only couriers can use this service; other roles get `403`. If the user service can't be reached, requests fail with `503`.

## Courier Locations

Locations are stored in a single Redis GEO set, `courier-locations` (`COURIER_LOCATIONS_KEY`), with `GEOADD`. Each courier is the member `courier-id-{courier_id}`, where `courier_id` is the courier's ID from the user service (not the user ID). Sending a new location overwrites the previous one.

Latitude must be between -85.05112878 and 85.05112878 (the range Redis GEO accepts) and longitude between -180 and 180; otherwise `422`. If Redis can't be reached, the request fails with `503`.

To inspect stored locations:

```bash
docker exec -it swift-drop-redis redis-cli -a redis --no-auth-warning GEOPOS courier-locations courier-id-{courier_id}
```

## Courier Availability

Online couriers are kept in the Redis set `couriers:online` (`COURIER_ONLINE_KEY`), using the same `courier-id-{courier_id}` members as the location index. The dispatch service only offers orders to couriers that are in this set and not in `couriers:busy`. If Redis can't be reached, the request fails with `503`.

## Nearby Orders

`GET /api/couriers/orders/nearby` lists orders that are `ready_for_pickup` and have no courier assigned, at restaurants close to the courier:

1. The courier's position is read from `courier-locations`. If the courier has never sent a location, the request fails with `409`.
2. Restaurants within `radius_km` (default 5, `NEARBY_ORDERS_DEFAULT_RADIUS_KM`; max 20, `NEARBY_ORDERS_MAX_RADIUS_KM`) are found with `GEOSEARCH` in the Redis GEO set `restaurant-locations` (`RESTAURANT_LOCATIONS_KEY`), written by the restaurant service. Only the nearest 1000 restaurants are considered.
3. Their waiting orders are fetched from the order service's `POST /internal/orders/ready-for-pickup/search`.
4. Orders are returned nearest restaurant first, and oldest ready first within a restaurant, up to `limit` (default 20, max 50).

Each order has `id`, `restaurant_id`, `distance_km` (from the courier to the restaurant), `total_price`, `delivery_address`, `items` (`item_name` and `quantity`), `created_at` and `ready_at`. The list is a snapshot; it doesn't reserve the orders. If Redis or the order service can't be reached, the request fails with `503`.

## Endpoints

| Method | Path | Description |
|---|---|---|
| PUT | `/api/couriers/location` | Update the current courier's location. Body: `{"latitude": 41.0082, "longitude": 28.9784}`. Returns `204` |
| PUT | `/api/couriers/online` | Mark the current courier online, so dispatch can find them. Returns `204` |
| PUT | `/api/couriers/offline` | Mark the current courier offline. Returns `204` |
| GET | `/api/couriers/orders/nearby` | List orders waiting for a courier near the current courier, nearest first. Optional `?radius_km=5&limit=20` |
