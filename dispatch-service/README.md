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
core/           settings, database session, Redis client, Kafka producer/consumer, shared dependencies
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

## Courier Search

On startup the service consumes the order events topic `order-events` (`KAFKA_ORDER_EVENTS_TOPIC`) as consumer group `dispatch-service` (`KAFKA_CONSUMER_GROUP_ID`). Only `order.status_updated` events are handled (read from the `event_type` header). When an order's status changes to `ready_for_pickup`, the service searches for couriers around the restaurant:

1. The restaurant's position is read from the Redis GEO set `restaurant-locations`, written by the restaurant service. If the restaurant has no stored position, the search is skipped and a warning is logged.
2. Couriers are searched in the Redis GEO set `courier-locations` (written by the courier service) with `GEOSEARCH`, first within 2 km, then within 5 km (`COURIER_SEARCH_RADII_KM`, default `[2.0, 5.0]`).
3. Only couriers in the `couriers:online` set and not in the `couriers:busy` set are kept. The first radius with at least one available courier wins, and its couriers are returned nearest first.
4. The result is published to the Kafka topic `dispatch-events` (`KAFKA_DISPATCH_EVENTS_TOPIC`), keyed by order ID, with the `event_type` header repeating the event type. One event is published per search, including searches that found nobody.

| Event type | When | `data` |
|---|---|---|
| `dispatch.courier_search_completed` | A courier search for a `ready_for_pickup` order finished | `order_id`, `restaurant_id`, `radius_km` (the radius the couriers were found in, `null` if none), `candidates` (list of `courier_id` and `distance_km`, nearest first; empty if none) |

Offsets are stored only after a message has been handled, so a restart replays unhandled events. Malformed events, and events whose search fails because Redis can't be reached, are logged and skipped.
