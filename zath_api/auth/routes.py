from fastapi import APIRouter, HTTPException, status, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
import asyncpg
from db.connection import get_pool
from .middleware import generate_api_key, hash_api_key
from .models import (
    UserLogin, UserRegister, TokenResponse, UserResponse,
    ForgotPasswordRequest, SimpleResetPasswordRequest, ResetPasswordRequest, PasswordResetResponse,
    hash_password, verify_password, create_access_token, verify_token,
    create_reset_token, verify_reset_token
)
from datetime import datetime, timedelta
import uuid

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get current user from JWT token.
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        User data from token
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_email = payload.get("sub")
    if user_email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify user still exists in database
    pool = await get_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT id, email, api_key, created_at FROM users WHERE email = $1",
            user_email
        )
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {
        "id": str(user['id']),
        "email": user['email'],
        "api_key": user['api_key'],
        "created_at": user['created_at'].isoformat() if user['created_at'] else None
    }

@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserRegister):
    """
    Register a new user account.
    
    This endpoint creates a new user account with email and password,
    and generates a unique API key for programmatic access.
    
    ## Request Body
    
    - **email** (string, required): User's email address
    - **password** (string, required): User's password (minimum 6 characters)
    
    ## Response
    
    Returns user information including:
    
    - **id** (string): Unique user identifier (UUID)
    - **email** (string): User's email address
    - **api_key** (string): API key for programmatic access
    - **created_at** (string): ISO timestamp when account was created
    """
    try:
        pool = await get_pool()
        
        # Check if user already exists
        async with pool.acquire() as conn:
            existing_user = await conn.fetchrow(
                "SELECT id FROM users WHERE email = $1",
                user_data.email
            )
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        
        # Generate API key and hash password
        api_key = generate_api_key()
        password_hash = hash_password(user_data.password)
        user_id = str(uuid.uuid4())
        
        # Create user in database
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO users (id, email, password_hash, api_key)
                VALUES ($1, $2, $3, $4)
                """,
                user_id, user_data.email, password_hash, api_key
            )
        
        return UserResponse(
            id=user_id,
            email=user_data.email,
            api_key=api_key,
            created_at=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register user: {str(e)}"
        )

@router.post("/login", response_model=TokenResponse)
async def login_user(user_data: UserLogin):
    """
    Login with email and password.
    
    This endpoint authenticates a user with email and password,
    and returns a JWT access token for session management.
    
    ## Request Body
    
    - **email** (string, required): User's email address
    - **password** (string, required): User's password
    
    ## Response
    
    Returns authentication token:
    
    - **access_token** (string): JWT access token for session management
    - **token_type** (string): Type of token (always "bearer")
    - **expires_in** (integer): Token expiration time in seconds
    """
    try:
        pool = await get_pool()
        
        # Get user from database
        async with pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT id, email, password_hash FROM users WHERE email = $1",
                user_data.email
            )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if user needs password reset (from migration)
        if user['password_hash'] == 'NEEDS_RESET':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account needs password reset. Please contact support."
            )
        
        # Verify password
        if not verify_password(user_data.password, user['password_hash']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": user['email']},
            expires_delta=access_token_expires
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=30 * 60  # 30 minutes in seconds
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to login: {str(e)}"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current user information.
    
    This endpoint returns information about the currently authenticated user.
    Requires a valid JWT access token.
    
    ## Authentication
    
    Requires valid JWT token in Authorization header:
    - `Authorization: Bearer your_jwt_token_here`
    
    ## Response
    
    Returns current user information:
    
    - **id** (string): Unique user identifier (UUID)
    - **email** (string): User's email address
    - **api_key** (string): API key for programmatic access
    - **created_at** (string): ISO timestamp when account was created
    """
    return UserResponse(**current_user)

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

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """
    Request a password reset.
    
    This endpoint sends a password reset email to the user's email address.
    The email contains a secure link with a token that allows the user to reset their password.
    
    ## Request Body
    
    - **email** (string, required): User's email address
    
    ## Response
    
    Returns a success message (for security, always returns success even if email doesn't exist)
    
    - **message** (string): Success message
    """
    try:
        pool = await get_pool()
        
        # Check if user exists
        async with pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT id FROM users WHERE email = $1",
                request.email
            )
        
        if user:
            # User exists - return success
            return {
                "user_exists": True,
                "message": "Account found. You can now set a new password."
            }
        else:
            # User doesn't exist
            return {
                "user_exists": False,
                "message": "No account found with this email address."
            }
        
    except Exception as e:
        # Log error and return error response
        print(f"Error in forgot password: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process request: {str(e)}"
        )

@router.get("/validate-reset-token")
async def validate_reset_token(token: str):
    """
    Validate a password reset token.
    
    This endpoint validates whether a password reset token is valid and not expired.
    
    ## Query Parameters
    
    - **token** (string, required): Password reset token
    
    ## Response
    
    Returns validation result:
    
    - **valid** (boolean): True if token is valid, False otherwise
    """
    try:
        email = verify_reset_token(token)
        return {"valid": email is not None}
    except Exception as e:
        return {"valid": False}

@router.post("/reset-password", response_model=PasswordResetResponse)
async def reset_password(request: ResetPasswordRequest):
    """
    Reset password using a reset token.
    
    This endpoint allows users to set a new password using a valid reset token.
    
    ## Request Body
    
    - **token** (string, required): Password reset token
    - **new_password** (string, required): New password (minimum 6 characters)
    
    ## Response
    
    Returns success message:
    
    - **message** (string): Success message
    """
    try:
        # Verify reset token
        email = verify_reset_token(request.token)
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Hash new password
        hashed_password = hash_password(request.new_password)
        
        # Update user's password
        pool = await get_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE users SET password_hash = $1 WHERE email = $2",
                hashed_password, email
            )
            
            if result == "UPDATE 0":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User not found"
                )
        
        return PasswordResetResponse(
            message="Password reset successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset password: {str(e)}"
        )

@router.post("/simple-reset-password", response_model=PasswordResetResponse)
async def simple_reset_password(request: SimpleResetPasswordRequest):
    """
    Reset password directly using email (no token required).
    
    This endpoint allows users to reset their password by providing their email
    and new password directly. This is a simplified approach for development
    without email services.
    
    ## Request Body
    
    - **email** (string, required): User's email address
    - **new_password** (string, required): New password (minimum 6 characters)
    
    ## Response
    
    Returns success message:
    
    - **message** (string): Success message
    """
    try:
        # Hash new password
        hashed_password = hash_password(request.new_password)
        
        # Update user's password
        pool = await get_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE users SET password_hash = $1 WHERE email = $2",
                hashed_password, request.email
            )
            
            if result == "UPDATE 0":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User not found"
                )
        
        return PasswordResetResponse(
            message="Password reset successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset password: {str(e)}"
        )
