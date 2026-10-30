import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

from core.proxy import forward, http_client
from core.routing import resolve_upstream

logging.basicConfig(level=logging.INFO, format="%(levelname)s:     %(name)s - %(message)s")

PROXY_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await http_client.aclose()


app = FastAPI(
    title="Swift Drop Gateway",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.api_route("/api/{path:path}", methods=PROXY_METHODS)
async def proxy(path: str, request: Request) -> Response:
    upstream = resolve_upstream(path)
    if upstream is None:
        return JSONResponse(status_code=404, content={"detail": "Not Found"})
    return await forward(request, upstream)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8080, reload=True)
