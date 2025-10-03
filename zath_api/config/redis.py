"""
Redis configuration for job queue management.

This module provides Redis client configuration and connection management
for the job queue system.
"""

import logging
import os
from typing import Optional

import redis.asyncio as redis
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Redis configuration with defaults
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")  # Optional password
REDIS_SSL = os.getenv("REDIS_SSL", "false").lower() == "true"  # SSL connection

# Create Redis client with configuration
redis_client: Optional[redis.Redis] = None

try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD,
        ssl=REDIS_SSL,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True,
        health_check_interval=30
    )
except Exception as e:
    logger.warning(f"Failed to initialize Redis client: {e}")
    redis_client = None


async def get_redis_client() -> redis.Redis:
    """
    Get the Redis client instance.
    
    Returns:
        Redis client instance
        
    Raises:
        ConnectionError: If Redis connection cannot be established
    """
    if redis_client is None:
        raise ConnectionError("Redis client not initialized")
    
    # Test connection
    try:
        await redis_client.ping()
        return redis_client
    except Exception as e:
        raise ConnectionError(f"Cannot connect to Redis: {e}")


async def test_redis_connection() -> bool:
    """
    Test Redis connection.
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        client = await get_redis_client()
        await client.ping()
        return True
    except Exception:
        return False
