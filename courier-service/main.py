import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from core.database import engine

logging.basicConfig(level=logging.INFO, format="%(levelname)s:     %(name)s - %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    engine.dispose()


app = FastAPI(
    title="Swift Drop Courier Service",
    version="1.0.0",
    lifespan=lifespan,
)

router = APIRouter(prefix="/api")

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8003, reload=True)
