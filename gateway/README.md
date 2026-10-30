# Gateway

Swift Drop's API gateway. It is the single entry point for clients: every request under `/api` is forwarded to the service that owns it, and the upstream response is returned unchanged. The gateway has no database and does no authentication itself; the `Authorization` header and all other request headers are passed through to the services.

## Tech Stack

- FastAPI
- httpx (async) for forwarding requests
- pydantic-settings for configuration

## Project Structure

```
core/config/    settings
core/routing.py route table mapping path prefixes to services
core/proxy.py   request forwarding to the upstream services
main.py         app entry point, health check and catch-all proxy route
```

## Setup

1. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and adjust the values if needed. All values have defaults, so `.env` is optional when the services run on their default ports.

   | Variable | Default | Description |
   |---|---|---|
   | `USER_SERVICE_URL` | `http://127.0.0.1:8000` | User service base URL |
   | `RESTAURANT_SERVICE_URL` | `http://127.0.0.1:8001` | Restaurant service base URL |
   | `UPSTREAM_TIMEOUT_SECONDS` | `10` | Timeout for requests to the services |

3. Start the user service and the restaurant service (see their READMEs), then start the gateway:

   ```bash
   python main.py
   ```

The gateway runs at http://127.0.0.1:8080.

## Routing

Requests are routed by the first path segment after `/api`. The path and query string are forwarded as-is.

| Path prefix | Service |
|---|---|
| `/api/auth/*` | User service |
| `/api/couriers/*` | User service |
| `/api/merchants/*` | User service |
| `/api/restaurants/*` | Restaurant service |
| `/api/categories/*` | Restaurant service |
| `/api/items/*` | Restaurant service |

For example, `POST http://127.0.0.1:8080/api/auth/login` is forwarded to `POST http://127.0.0.1:8000/api/auth/login`, and `GET http://127.0.0.1:8080/api/restaurants/1` to `GET http://127.0.0.1:8001/api/restaurants/1`.

To add a new service, add its URL to `core/config/settings.py` and its path prefixes to `ROUTES` in `core/routing.py`.

## Responses Produced by the Gateway

| Status | When |
|---|---|
| `404` | The path doesn't match any route |
| `503` | The target service can't be reached |
| `504` | The target service didn't respond within `UPSTREAM_TIMEOUT_SECONDS` |

All other responses come from the services themselves.

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Returns `{"status": "ok"}` if the gateway is running (doesn't check the services) |

API docs are not served by the gateway; use each service's `/docs` page.
