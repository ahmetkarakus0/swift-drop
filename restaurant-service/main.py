import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from core.database import engine
from core.user_service import user_service_client
from routes.category_route import router as category_router
from routes.item_route import router as item_router
from routes.restaurant_route import router as restaurant_router

logging.basicConfig(level=logging.INFO, format="%(levelname)s:     %(name)s - %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    user_service_client.close()
    engine.dispose()


app = FastAPI(
    title="Swift Drop Restaurant Service",
    version="1.0.0",
    lifespan=lifespan,
)

router = APIRouter(prefix="/api")
router.include_router(restaurant_router)
router.include_router(category_router)
router.include_router(item_router)

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)
