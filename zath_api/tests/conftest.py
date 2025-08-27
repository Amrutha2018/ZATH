"""
Test configuration and shared fixtures for ZATH API tests
"""
import pytest
import asyncio
import aiohttp
import os
from typing import AsyncGenerator

# Set environment variables for testing
os.environ.update({
    'DB_HOST': 'localhost',
    'DB_PORT': '5432',
    'DB_NAME': 'zathdb',
    'DB_USER': 'amruthae',
    'DB_PASS': ''
})

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def http_client() -> AsyncGenerator[aiohttp.ClientSession, None]:
    """Provide an HTTP client for testing API endpoints."""
    async with aiohttp.ClientSession() as session:
        yield session

@pytest.fixture
def base_url() -> str:
    """Base URL for API testing."""
    return "http://localhost:8000"

@pytest.fixture
def test_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com"
    }
