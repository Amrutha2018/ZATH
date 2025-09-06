import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
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

# Define security schemes for API documentation
security_schemes = {
    "ApiKeyAuth": {
        "type": "apiKey",
        "in": "header",
        "name": "X-API-Key",
        "description": "Enter your API key"
    },
    "BearerAuth": {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "API Key",
        "description": "Enter your API key as Bearer token"
    }
}

app = FastAPI(
    title="ZATH API",
    description="Asynchronous Job Processing System",
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "User authentication and API key management"
        },
        {
            "name": "Jobs",
            "description": "Job creation, status checking, and management"
        }
    ]
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add auth middleware
app.add_middleware(AuthMiddleware)

# Customize OpenAPI schema to include security schemes
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    from fastapi.openapi.utils import get_openapi
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = security_schemes
    
    # Add security requirements to protected endpoints
    for path, path_item in openapi_schema["paths"].items():
        # Skip public paths
        if path in ["/", "/docs", "/redoc", "/openapi.json", "/auth/register", "/auth/login", "/auth/forgot-password", "/auth/simple-reset-password"]:
            continue
            
        # Add security to all methods in protected paths
        for method, operation in path_item.items():
            if method in ["get", "post", "put", "delete", "patch"]:
                operation["security"] = [
                    {"ApiKeyAuth": []},
                    {"BearerAuth": []}
                ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

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