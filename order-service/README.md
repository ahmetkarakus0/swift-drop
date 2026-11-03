# Order Service

Swift Drop's order service. Lets customers fill baskets and place orders from them. It owns the `order_db` PostgreSQL database.

## Tech Stack

- FastAPI
- SQLAlchemy 2 + PostgreSQL (psycopg 3)
- Alembic for migrations
- httpx for calling the user service and the restaurant service
- Kafka (confluent-kafka) for publishing order events

## Project Structure

```
core/           settings, database session, user/restaurant service clients, Kafka producer, shared dependencies
models/         SQLAlchemy models (baskets, basket items, orders, order items)
schemas/        Pydantic request/response models
repositories/   database access
services/       business logic
routes/         API endpoints
alembic/        database migrations
```

## Setup

1. Start PostgreSQL and Kafka from the repository root:

   ```bash
   docker compose up -d
   ```

2. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and fill in the values. `USER_SERVICE_URL` and `RESTAURANT_SERVICE_URL` must point to running services. `KAFKA_BOOTSTRAP_SERVERS` defaults to `localhost:9092`, the Kafka broker from `docker-compose.yml`.

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

## Events

Order events are published to the Kafka topic `order-events` (`KAFKA_ORDER_EVENTS_TOPIC`). The message key is the order ID, so all events of one order go to the same partition and are consumed in order. The value is JSON and the `event_type` header repeats the event type.

| Event type | When | `data` |
|---|---|---|
| `order.created` | An order is placed | The full order, same shape as the `POST /api/orders` response |
| `order.status_updated` | An order's status changes (accept, prepare, ready for pickup, on the way, cancel) | `order_id`, `user_id`, `restaurant_id`, `courier_id`, `previous_status`, `status`, `updated_at` |
| `order.courier_assigned` | A courier is assigned to a `ready_for_pickup` order. The status doesn't change | `order_id`, `user_id`, `restaurant_id`, `courier_id`, `status`, `updated_at` |

Every event has this envelope:

```json
{
  "event_id": "uuid",
  "occurred_at": "2026-10-31T20:09:50.856409Z",
  "event_type": "order.status_updated",
  "data": {}
}
```

Events are published after the database commit and publishing never fails the request. If Kafka is down, the order is still saved, and the failed delivery is logged. Undelivered events are lost; consumers should not treat the topic as a complete record. Unsent events are flushed on shutdown.

The topic is created automatically by the first published event.

### Inspecting events

`docker compose up -d` also starts Kafbat UI at http://localhost:8090 (`KAFKA_UI_PORT`). Open **Topics → order-events → Messages** to browse events, including their keys and headers.

From the command line, using the tools inside the Kafka container:

```bash
# list topics
docker exec swift-drop-kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list

# print all order events from the beginning and keep following new ones (Ctrl+C to stop)
docker exec -it swift-drop-kafka /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic order-events --from-beginning --property print.key=true --property print.headers=true
```

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
| POST | `/internal/orders/ready-for-pickup/search` | List `ready_for_pickup` orders with no courier assigned from the given restaurants, with their items, oldest ready first. Body: `{"restaurant_ids": ["..."]}` (at most 1000). Used by the courier service |
| PUT | `/internal/orders/{order_id}/courier` | Assign a courier to a `ready_for_pickup` order. Body: `{"courier_id": "..."}`. Returns `404` if the order doesn't exist and `409` if it isn't ready for pickup or another courier already has it. Repeating it for the same courier returns the order unchanged. Used by the courier service |
| PUT | `/internal/couriers/{courier_id}/orders/{order_id}/on-the-way` | Change a courier's order from `ready_for_pickup` to `on_the_way`. Returns `404` if the order isn't assigned to the courier and `409` if it isn't ready for pickup. Used by the courier service |
| GET | `/internal/restaurants/{restaurant_id}/orders` | List a restaurant's orders with their items, newest first. Optional `?status=` filter. Used by the restaurant service |
| PUT | `/internal/restaurants/{restaurant_id}/orders/{order_id}/accept` | Change a restaurant's order from `pending` to `confirmed`. Returns `404` if the order doesn't belong to the restaurant and `409` if it isn't pending. Used by the restaurant service |
| PUT | `/internal/restaurants/{restaurant_id}/orders/{order_id}/prepare` | Change a restaurant's order from `confirmed` to `preparing`. Returns `404` if the order doesn't belong to the restaurant and `409` if it isn't confirmed. Used by the restaurant service |
| PUT | `/internal/restaurants/{restaurant_id}/orders/{order_id}/ready-for-pickup` | Change a restaurant's order from `preparing` to `ready_for_pickup`. Returns `404` if the order doesn't belong to the restaurant and `409` if it isn't preparing. Used by the restaurant service |
| PUT | `/internal/restaurants/{restaurant_id}/orders/{order_id}/cancel` | Change a restaurant's order to `cancelled`. Allowed from `pending`, `confirmed` or `preparing`; otherwise `409`. Returns `404` if the order doesn't belong to the restaurant. Used by the restaurant service |

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
