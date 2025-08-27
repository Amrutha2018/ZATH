from fastapi import FastAPI, Request, HTTPException
from contextlib import asynccontextmanager
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse

from db.connection import init_db_pool, close_db_pool
from auth.middleware import verify_api_key
from auth.routes import router as auth_router
from api.routes import api_router

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
    print("🌱 Initializing DB connection pool...")
    await init_db_pool()

    yield  # App runs here

    print("🛑 Closing DB connection pool...")
    await close_db_pool()

app = FastAPI(lifespan=lifespan)

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