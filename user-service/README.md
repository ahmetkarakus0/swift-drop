# User Service

Swift Drop's user service. Handles registration and authentication for customers and couriers, along with their profiles and addresses. It owns the `user_db` PostgreSQL database.

## Tech Stack

- FastAPI
- SQLAlchemy 2 + PostgreSQL (psycopg 3)
- Alembic for migrations
- JWT (PyJWT) for authentication, bcrypt for password hashing

## Project Structure

```
core/           settings, database session, security helpers, shared dependencies
models/         SQLAlchemy models (users, customers, couriers, merchants, addresses)
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

3. Copy `.env.example` to `.env` and fill in the values. `JWT_SECRET_KEY` should be a long random string.

4. Apply migrations and start the service:

   ```bash
   alembic upgrade head
   python main.py
   ```

5. (Optional) Seed an admin user from `ADMIN_EMAIL` and `ADMIN_PASSWORD` in `.env`. Running it again does nothing if the user already exists:

   ```bash
   python -m seeds.admin
   ```

API docs are available at http://127.0.0.1:8000/docs.

## Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/api/auth/register/customer` | Register a customer with profile and address |
| POST | `/api/auth/register/courier` | Register a courier with profile, vehicle and address |
| POST | `/api/auth/register/merchant` | Register a merchant with business info and address (starts as `pending`) |
| GET | `/api/auth/verify?token=...` | Verifies the user's email using the link created at registration |
| POST | `/api/auth/login` | Returns an access token (30 min) and a refresh token (7 days) |
| POST | `/api/auth/refresh` | Exchanges a refresh token for a new token pair; the old refresh token stops working |
| POST | `/api/auth/logout` | Revokes the access token (header) and the refresh token (body) |
| GET | `/api/auth/me` | Returns the current user with their `customer_id`, `courier_id` or `merchant_id` (requires `Authorization: Bearer <access_token>`). Returns `403` if the user is inactive, unverified, an unverified courier or an unverified merchant |
| POST | `/api/couriers/{courier_id}/verify` | Marks a courier as verified (admin only) |
| POST | `/api/merchants/{merchant_id}/verify` | Marks a merchant as verified (admin only) |
| PATCH | `/api/merchants/{merchant_id}/status` | Approves or rejects a merchant with `{"status": "approved"}` or `{"status": "rejected"}` (admin only) |
