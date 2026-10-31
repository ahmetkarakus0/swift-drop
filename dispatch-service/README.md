# Dispatch Service

Swift Drop's dispatch service. It owns the `dispatch_db` PostgreSQL database.

## Tech Stack

- FastAPI
- SQLAlchemy 2 + PostgreSQL (psycopg 3)
- Alembic for migrations
- Redis
- Kafka (confluent-kafka)

## Project Structure

```
core/           settings, database session, Redis client, Kafka producer, shared dependencies
models/         SQLAlchemy models
schemas/        Pydantic request/response models
repositories/   database access
services/       business logic
routes/         API endpoints
alembic/        database migrations
```

## Setup

1. Start PostgreSQL, Redis and Kafka from the repository root:

   ```bash
   docker compose up -d
   ```

2. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and fill in the values. `REDIS_URL` uses the Redis from `docker-compose.yml` (password `REDIS_PASSWORD`). `KAFKA_BOOTSTRAP_SERVERS` defaults to `localhost:9092`, the Kafka broker from `docker-compose.yml`.

4. Apply migrations and start the service:

   ```bash
   alembic upgrade head
   python main.py
   ```

API docs are available at http://127.0.0.1:8004/docs.
