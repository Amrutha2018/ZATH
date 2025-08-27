from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel, EmailStr
import asyncpg
from db.connection import get_pool
from .middleware import generate_api_key, hash_api_key

router = APIRouter(prefix="/auth", tags=["Authentication"])

class UserCreate(BaseModel):
    email: EmailStr

class UserResponse(BaseModel):
    id: str
    email: str
    api_key: str
    created_at: str

@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate):
    """Register a new user and generate API key"""
    
    pool = await get_pool()
    
    # Check if user already exists
    async with pool.acquire() as conn:
        existing_user = await conn.fetchrow(
            "SELECT id FROM users WHERE email = $1",
            user_data.email
        )
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Generate API key
        api_key = generate_api_key()
        
        # Insert new user
        user = await conn.fetchrow(
            """
            INSERT INTO users (id, email, api_key) 
            VALUES (gen_random_uuid(), $1, $2)
            RETURNING id, email, api_key, created_at
            """,
            user_data.email, api_key
        )
    
    return UserResponse(
        id=str(user['id']),
        email=user['email'],
        api_key=user['api_key'],
        created_at=user['created_at'].isoformat()
    )

@router.post("/regenerate-key", response_model=UserResponse)
async def regenerate_api_key(request: Request):
    """Regenerate API key for authenticated user"""
    
    if not hasattr(request.state, 'user'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    pool = await get_pool()
    new_api_key = generate_api_key()
    
    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            """
            UPDATE users 
            SET api_key = $1 
            WHERE id = $2
            RETURNING id, email, api_key, created_at
            """,
            new_api_key, request.state.user['id']
        )
    
    return UserResponse(
        id=str(user['id']),
        email=user['email'],
        api_key=user['api_key'],
        created_at=user['created_at'].isoformat()
    )
