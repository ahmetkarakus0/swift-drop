from fastapi import FastAPI, APIRouter

from routes.auth_route import router as auth_router

app = FastAPI(
    title="Swift Drop User Service",
    version="1.0.0"
)

router = APIRouter(prefix="/api")
router.include_router(auth_router)

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
