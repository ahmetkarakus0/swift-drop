import logging

import httpx
from fastapi import Request
from fastapi.responses import JSONResponse, Response

from core.config.settings import settings

logger = logging.getLogger(__name__)

HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}

# httpx decodes the body and the length is recalculated, so these must not be copied as-is.
EXCLUDED_REQUEST_HEADERS = HOP_BY_HOP_HEADERS | {"host", "content-length"}
EXCLUDED_RESPONSE_HEADERS = HOP_BY_HOP_HEADERS | {"content-encoding", "content-length"}

http_client = httpx.AsyncClient(timeout=settings.UPSTREAM_TIMEOUT_SECONDS)


def _forward_headers(request: Request) -> dict[str, str]:
    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in EXCLUDED_REQUEST_HEADERS
    }
    client_host = request.client.host if request.client else None
    if client_host:
        existing = request.headers.get("x-forwarded-for")
        headers["x-forwarded-for"] = f"{existing}, {client_host}" if existing else client_host
    headers["x-forwarded-host"] = request.headers.get("host", "")
    headers["x-forwarded-proto"] = request.url.scheme
    return headers


async def forward(request: Request, upstream: str) -> Response:
    url = f"{upstream.rstrip('/')}{request.url.path}"
    try:
        upstream_response = await http_client.request(
            method=request.method,
            url=url,
            params=request.query_params.multi_items(),
            headers=_forward_headers(request),
            content=await request.body(),
        )
    except httpx.TimeoutException:
        logger.warning("Upstream timed out: %s %s", request.method, url)
        return JSONResponse(status_code=504, content={"detail": "Upstream service timed out"})
    except httpx.RequestError as exc:
        logger.warning("Upstream unavailable: %s %s (%s)", request.method, url, exc)
        return JSONResponse(status_code=503, content={"detail": "Upstream service unavailable"})

    response = Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
    )
    for key, value in upstream_response.headers.multi_items():
        if key.lower() not in EXCLUDED_RESPONSE_HEADERS:
            response.headers.append(key, value)
    return response
