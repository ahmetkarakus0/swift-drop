from fastapi import FastAPI


app = FastAPI(
    title="Swift Drop Restaurant Service",
    version="1.0.0"
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)