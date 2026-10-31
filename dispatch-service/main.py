import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from core.config.settings import settings
from core.database import engine
from core.kafka import kafka_producer
from core.redis import redis_client

logging.basicConfig(level=logging.INFO, format="%(levelname)s:     %(name)s - %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    remaining = kafka_producer.flush(settings.KAFKA_FLUSH_TIMEOUT_SECONDS)
    if remaining:
        logger.warning("%d dispatch events were not delivered to Kafka", remaining)
    redis_client.close()
    engine.dispose()


app = FastAPI(
    title="Swift Drop Dispatch Service",
    version="1.0.0",
    lifespan=lifespan,
)

router = APIRouter(prefix="/api")

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8004, reload=True)
