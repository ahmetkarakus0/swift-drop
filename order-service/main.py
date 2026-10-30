import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from core.database import engine
from core.user_service import user_service_client

logging.basicConfig(level=logging.INFO, format="%(levelname)s:     %(name)s - %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    user_service_client.close()
    engine.dispose()


app = FastAPI(
    title="Swift Drop Order Service",
    version="1.0.0",
    lifespan=lifespan,
)

router = APIRouter(prefix="/api")

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8002, reload=True)
