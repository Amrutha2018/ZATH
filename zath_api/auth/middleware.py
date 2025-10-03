from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import asyncpg
from db.connection import get_pool
import secrets
import hashlib

# Skip auth for these paths
PUBLIC_PATHS = {
    "/", "/docs", "/redoc", "/openapi.json", 
    "/auth/register", "/auth/login", 
    "/auth/forgot-password", "/auth/simple-reset-password", "/auth/validate-reset-token", "/auth/reset-password"
}

async def verify_api_key(request: Request):
    """Middleware to verify API key for all requests"""
    
    # Skip auth for public paths and OPTIONS requests (CORS preflight)
    if request.url.path in PUBLIC_PATHS or request.method == "OPTIONS":
        return
    
    # Check if this is a JWT-protected endpoint
    if request.url.path == "/auth/me":
        # Let the endpoint handle JWT authentication
        return
    
    # Get API key from header
    api_key = request.headers.get("X-API-Key") or request.headers.get("Authorization")
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    # Clean up Authorization header if it has "Bearer " prefix
    if api_key.startswith("Bearer "):
        api_key = api_key[7:]
    
    # Verify API key in database
    pool = await get_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT id, email FROM users WHERE api_key = $1",
            api_key
        )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    # Add user info to request state for use in endpoints
    request.state.user = user

def generate_api_key() -> str:
    """Generate a secure API key"""
    return secrets.token_urlsafe(32)

def hash_api_key(api_key: str) -> str:
    """Hash API key for storage (optional security enhancement)"""
    return hashlib.sha256(api_key.encode()).hexdigest()
