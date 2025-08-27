from fastapi import FastAPI
from contextlib import asynccontextmanager

from db.connection import init_db_pool, close_db_pool

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🌱 Initializing DB connection pool...")
    await init_db_pool()

    yield  # App runs here

    print("🛑 Closing DB connection pool...")
    await close_db_pool()

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def read_root():
    return {"message": "ZATH is listening..."}