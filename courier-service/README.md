# Courier Service

Swift Drop's courier service. It owns the `courier_db` PostgreSQL database.

## Tech Stack

- FastAPI
- SQLAlchemy 2 + PostgreSQL (psycopg 3)
- Alembic for migrations
- Redis for courier locations
- httpx for calling the user service

## Project Structure

```
core/           settings, database session, Redis client, user service client, shared dependencies
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

3. Copy `.env.example` to `.env` and fill in the values. `REDIS_URL` uses the Redis from `docker-compose.yml` (password `REDIS_PASSWORD`). `USER_SERVICE_URL` must point to a running user service.

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

## Endpoints

| Method | Path | Description |
|---|---|---|
| PUT | `/api/couriers/location` | Update the current courier's location. Body: `{"latitude": 41.0082, "longitude": 28.9784}`. Returns `204` |
