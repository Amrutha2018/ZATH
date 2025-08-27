"""
Pytest-style authentication tests for ZATH API
"""
import pytest
import json
import time
from typing import Dict, Any

@pytest.mark.integration
class TestAuthentication:
    """Test suite for authentication functionality"""
    
    async def test_health_check(self, http_client, base_url):
        """Test server health endpoint"""
        async with http_client.get(f"{base_url}/") as response:
            assert response.status == 200
            data = await response.json()
            assert "ZATH is listening" in data["message"]
    
    async def test_user_registration(self, http_client, base_url):
        """Test user registration with API key generation"""
        user_data = {"email": f"test-{int(time.time())}@example.com"}
        
        async with http_client.post(
            f"{base_url}/auth/register",
            json=user_data
        ) as response:
            assert response.status == 200
            data = await response.json()
            assert "api_key" in data
            assert "id" in data
            assert data["email"] == user_data["email"]
            return data["api_key"]
    
    async def test_protected_endpoint_no_auth(self, http_client, base_url):
        """Test that protected endpoints require authentication"""
        async with http_client.get(f"{base_url}/protected") as response:
            assert response.status == 401
            data = await response.json()
            assert "API key required" in data["detail"]
    
    async def test_protected_endpoint_with_x_api_key(self, http_client, base_url):
        """Test protected endpoint with X-API-Key header"""
        # First register a user
        user_data = {"email": f"test-{int(time.time())}@example.com"}
        async with http_client.post(
            f"{base_url}/auth/register",
            json=user_data
        ) as response:
            user_info = await response.json()
            api_key = user_info["api_key"]
        
        # Test protected endpoint
        headers = {"X-API-Key": api_key}
        async with http_client.get(
            f"{base_url}/protected",
            headers=headers
        ) as response:
            assert response.status == 200
            data = await response.json()
            assert "user_id" in data
            assert "user_email" in data
    
    async def test_protected_endpoint_with_authorization_header(self, http_client, base_url):
        """Test protected endpoint with Authorization header"""
        # First register a user
        user_data = {"email": f"test-{int(time.time())}@example.com"}
        async with http_client.post(
            f"{base_url}/auth/register",
            json=user_data
        ) as response:
            user_info = await response.json()
            api_key = user_info["api_key"]
        
        # Test protected endpoint
        headers = {"Authorization": f"Bearer {api_key}"}
        async with http_client.get(
            f"{base_url}/protected",
            headers=headers
        ) as response:
            assert response.status == 200
            data = await response.json()
            assert "user_id" in data
            assert "user_email" in data
    
    async def test_invalid_api_key(self, http_client, base_url):
        """Test that invalid API keys are rejected"""
        headers = {"X-API-Key": "invalid-key-123"}
        async with http_client.get(
            f"{base_url}/protected",
            headers=headers
        ) as response:
            assert response.status == 401
            data = await response.json()
            assert "Invalid API key" in data["detail"]
    
    async def test_api_key_regeneration(self, http_client, base_url):
        """Test API key regeneration"""
        # First register a user
        user_data = {"email": f"test-{int(time.time())}@example.com"}
        async with http_client.post(
            f"{base_url}/auth/register",
            json=user_data
        ) as response:
            user_info = await response.json()
            old_api_key = user_info["api_key"]
        
        # Regenerate API key
        headers = {"X-API-Key": old_api_key}
        async with http_client.post(
            f"{base_url}/auth/regenerate-key",
            headers=headers
        ) as response:
            assert response.status == 200
            data = await response.json()
            new_api_key = data["api_key"]
            assert new_api_key != old_api_key
        
        # Verify old key no longer works
        headers = {"X-API-Key": old_api_key}
        async with http_client.get(
            f"{base_url}/protected",
            headers=headers
        ) as response:
            assert response.status == 401
        
        # Verify new key works
        headers = {"X-API-Key": new_api_key}
        async with http_client.get(
            f"{base_url}/protected",
            headers=headers
        ) as response:
            assert response.status == 200
    
    async def test_duplicate_registration(self, http_client, base_url):
        """Test that duplicate email registration is prevented"""
        user_data = {"email": f"test-{int(time.time())}@example.com"}
        
        # First registration should succeed
        async with http_client.post(
            f"{base_url}/auth/register",
            json=user_data
        ) as response:
            assert response.status == 200
        
        # Second registration with same email should fail
        async with http_client.post(
            f"{base_url}/auth/register",
            json=user_data
        ) as response:
            assert response.status == 400
            data = await response.json()
            assert "already exists" in data["detail"]
    
    async def test_invalid_email_format(self, http_client, base_url):
        """Test that invalid email formats are rejected"""
        invalid_data = {"email": "invalid-email"}
        
        async with http_client.post(
            f"{base_url}/auth/register",
            json=invalid_data
        ) as response:
            assert response.status == 422  # Validation error
    
    async def test_regenerate_key_without_auth(self, http_client, base_url):
        """Test that API key regeneration requires authentication"""
        async with http_client.post(f"{base_url}/auth/regenerate-key") as response:
            assert response.status == 401
            data = await response.json()
            assert "API key required" in data["detail"]

@pytest.mark.unit
class TestAuthenticationUnit:
    """Unit tests for authentication components"""
    
    def test_api_key_generation(self):
        """Test API key generation utility"""
        from auth.middleware import generate_api_key
        
        key1 = generate_api_key()
        key2 = generate_api_key()
        
        assert len(key1) > 20  # Should be reasonably long
        assert key1 != key2  # Should be unique
        assert isinstance(key1, str)
    
    def test_api_key_hashing(self):
        """Test API key hashing utility"""
        from auth.middleware import hash_api_key
        
        key = "test-key"
        hashed = hash_api_key(key)
        
        assert len(hashed) == 64  # SHA256 hex length
        assert hashed != key  # Should be different from original
        assert isinstance(hashed, str)
