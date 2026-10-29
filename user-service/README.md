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
models/         SQLAlchemy models (users, customers, couriers, addresses)
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

API docs are available at http://127.0.0.1:8000/docs.

## Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/api/auth/register/customer` | Register a customer with profile and address |
| POST | `/api/auth/register/courier` | Register a courier with profile, vehicle and address |
| POST | `/api/auth/login` | Returns a JWT access token |
| GET | `/api/auth/me` | Returns the current user (requires `Authorization: Bearer <token>`) |
