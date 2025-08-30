"""
Authentication models and utilities for ZATH API.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime, timedelta, timezone
import bcrypt
from jose import JWTError, jwt
import os

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class UserLogin(BaseModel):
    """
    Model for user login request.
    
    Attributes:
        email: User's email address
        password: User's password
    """
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=6, description="User's password")

class UserRegister(BaseModel):
    """
    Model for user registration request.
    
    Attributes:
        email: User's email address
        password: User's password (minimum 6 characters)
    """
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=6, description="User's password (minimum 6 characters)")

class TokenResponse(BaseModel):
    """
    Model for authentication token response.
    
    Attributes:
        access_token: JWT access token
        token_type: Type of token (always "bearer")
        expires_in: Token expiration time in seconds
    """
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Type of token")
    expires_in: int = Field(..., description="Token expiration time in seconds")

class UserResponse(BaseModel):
    """
    Model for user information response.
    
    Attributes:
        id: User's unique identifier
        email: User's email address
        api_key: User's API key for programmatic access
        created_at: When the user was created
    """
    id: str = Field(..., description="User's unique identifier")
    email: str = Field(..., description="User's email address")
    api_key: str = Field(..., description="User's API key for programmatic access")
    created_at: str = Field(..., description="When the user was created")

class ForgotPasswordRequest(BaseModel):
    """
    Model for forgot password request.
    
    Attributes:
        email: User's email address
    """
    email: EmailStr = Field(..., description="User's email address")

class SimpleResetPasswordRequest(BaseModel):
    """
    Model for simple password reset request.
    
    Attributes:
        email: User's email address
        new_password: New password (minimum 6 characters)
    """
    email: EmailStr = Field(..., description="User's email address")
    new_password: str = Field(..., min_length=6, description="New password (minimum 6 characters)")

class ResetPasswordRequest(BaseModel):
    """
    Model for password reset request.
    
    Attributes:
        token: Password reset token
        new_password: New password (minimum 6 characters)
    """
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=6, description="New password (minimum 6 characters)")

class PasswordResetResponse(BaseModel):
    """
    Model for password reset response.
    
    Attributes:
        message: Success message
    """
    message: str = Field(..., description="Success message")

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        password: Plain text password to verify
        hashed_password: Hashed password to check against
        
    Returns:
        True if password matches, False otherwise
    """
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration time delta
        
    Returns:
        JWT token string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token data or None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def create_reset_token(email: str) -> str:
    """
    Create a password reset token.
    
    Args:
        email: User's email address
        
    Returns:
        Password reset token
    """
    # Create a token that expires in 1 hour
    expires_delta = timedelta(hours=1)
    return create_access_token(
        data={"sub": email, "type": "password_reset"}, 
        expires_delta=expires_delta
    )

def verify_reset_token(token: str) -> Optional[str]:
    """
    Verify a password reset token.
    
    Args:
        token: Password reset token to verify
        
    Returns:
        Email address if token is valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        token_type = payload.get("type")
        
        if email and token_type == "password_reset":
            return email
        return None
    except JWTError:
        return None

