import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger("e2e.http")


class ApiClient:
    """HTTP client for a single service. Every method returns the raw response so cases can assert on it."""

    def __init__(self, base_url: str, name: str, timeout: float):
        self.name = name
        self._client = httpx.Client(
            base_url=base_url,
            timeout=timeout,
            event_hooks={"response": [self._log_response]},
        )

    def request(
        self,
        method: str,
        path: str,
        *,
        token: Optional[str] = None,
        json: Any = None,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> httpx.Response:
        merged_headers = dict(headers or {})
        if token is not None:
            merged_headers["Authorization"] = f"Bearer {token}"
        return self._client.request(method, path, json=json, params=params, headers=merged_headers)

    def get(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("POST", path, **kwargs)

    def patch(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("PATCH", path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("PUT", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("DELETE", path, **kwargs)

    def is_reachable(self, path: str = "/openapi.json") -> bool:
        try:
            self._client.get(path)
        except httpx.TransportError:
            return False
        return True

    def close(self) -> None:
        self._client.close()

    def _log_response(self, response: httpx.Response) -> None:
        request = response.request
        response.read()
        logger.info(
            "[%s] %s %s -> %s %s",
            self.name,
            request.method,
            request.url,
            response.status_code,
            response.text[:2000],
        )


def expect_status(response: httpx.Response, expected: int) -> httpx.Response:
    """Asserts the status code and shows the response body when it doesn't match."""
    assert response.status_code == expected, (
        f"{response.request.method} {response.request.url} returned {response.status_code}, "
        f"expected {expected}. Body: {response.text}"
    )
    return response
