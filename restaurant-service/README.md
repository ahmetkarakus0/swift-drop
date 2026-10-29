# Restaurant Service

Swift Drop's restaurant service. Lets merchants manage their restaurants, menu categories and items. It owns the `restaurant_db` PostgreSQL database.

## Tech Stack

- FastAPI
- SQLAlchemy 2 + PostgreSQL (psycopg 3)
- Alembic for migrations
- httpx for calling the user service

## Project Structure

```
core/           settings, database session, user service client, shared dependencies
models/         SQLAlchemy models (restaurants, categories, items)
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

3. Copy `.env.example` to `.env` and fill in the values. `USER_SERVICE_URL` must point to a running user service.

4. Apply migrations and start the service:

   ```bash
   alembic upgrade head
   python main.py
   ```

API docs are available at http://127.0.0.1:8001/docs.

## Authentication

Every endpoint requires `Authorization: Bearer <access_token>`, using an access token issued by the user service. The token is checked by calling the user service's `GET /api/auth/me`, so the user service must be running.

Only merchants can use this service. Requests are rejected with `403` if the user is not a merchant, or if the user service considers them ineligible (inactive, email not verified, or merchant not verified by an admin). If the user service can't be reached, requests fail with `503`.

Merchants can only see and change their own restaurants, categories and items; anything else returns `404`.

## Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/api/restaurants` | Create a restaurant |
| GET | `/api/restaurants` | List the merchant's restaurants |
| GET | `/api/restaurants/{restaurant_id}` | Get a restaurant with its categories and their items |
| PATCH | `/api/restaurants/{restaurant_id}` | Update a restaurant (only the sent fields change) |
| DELETE | `/api/restaurants/{restaurant_id}` | Deactivate a restaurant along with its categories and items; nothing is removed from the database |
| POST | `/api/restaurants/{restaurant_id}/categories` | Create a category |
| GET | `/api/restaurants/{restaurant_id}/categories` | List a restaurant's categories |
| GET | `/api/categories/{category_id}` | Get a category with its items |
| PATCH | `/api/categories/{category_id}` | Update a category |
| DELETE | `/api/categories/{category_id}` | Delete a category and its items |
| POST | `/api/categories/{category_id}/items` | Create an item |
| GET | `/api/categories/{category_id}/items` | List a category's items |
| GET | `/api/items/{item_id}` | Get an item |
| PATCH | `/api/items/{item_id}` | Update an item |
| DELETE | `/api/items/{item_id}` | Delete an item |
