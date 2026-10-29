from contextlib import asynccontextmanager

from fastapi import FastAPI, APIRouter

from core.database import engine
from core.redis import redis_client
from routes.auth_route import router as auth_router
from routes.health_route import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    redis_client.close()
    engine.dispose()


app = FastAPI(
    title="Swift Drop User Service",
    version="1.0.0",
    lifespan=lifespan,
)

router = APIRouter(prefix="/api")
router.include_router(auth_router)

app.include_router(router)
app.include_router(health_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
