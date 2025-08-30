import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse

from db.connection import init_db_pool, close_db_pool
from auth.middleware import verify_api_key
from auth.routes import router as auth_router
from api.routes import api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            await verify_api_key(request)
        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail}
            )
        
        response = await call_next(request)
        return response

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🌱 Initializing DB connection pool...")
    await init_db_pool()

    yield  # App runs here

    logger.info("🛑 Closing DB connection pool...")
    await close_db_pool()

app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add auth middleware
app.add_middleware(AuthMiddleware)

# Include auth routes
app.include_router(auth_router)

# Include all API routes
app.include_router(api_router)

@app.get("/")
async def read_root():
    return {"message": "ZATH is listening..."}

# Example protected endpoint
@app.get("/protected")
async def protected_endpoint(request: Request):
    user = request.state.user
    return {
        "message": "This is a protected endpoint!",
        "user_id": user['id'],
        "user_email": user['email']
    }