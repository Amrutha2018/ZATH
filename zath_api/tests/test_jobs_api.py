"""
Tests for Jobs API endpoints
"""
import pytest
import json
import time
from typing import Dict, Any

@pytest.mark.integration
class TestJobsAPI:
    """Test suite for jobs API functionality"""
    
    async def test_create_job_valid_data(self, http_client, base_url):
        """Test creating job with valid data"""
        # First register a user to get API key
        user_data = {"email": f"test-{int(time.time())}@example.com"}
        async with http_client.post(
            f"{base_url}/auth/register",
            json=user_data
        ) as response:
            user_info = await response.json()
            api_key = user_info["api_key"]
        
        # Test job creation
        job_data = {
            "task_type": "email_send",
            "payload": {"to": "user@example.com", "subject": "Hello"},
            "callback_url": "https://webhook.site/abc123"
        }
        
        headers = {"X-API-Key": api_key}
        async with http_client.post(
            f"{base_url}/api/jobs",
            json=job_data,
            headers=headers
        ) as response:
            assert response.status == 202
            data = await response.json()
            assert "job_id" in data
            assert data["status"] == "queued"
            assert "created_at" in data
    
    async def test_create_job_without_callback(self, http_client, base_url):
        """Test creating job without callback_url"""
        # First register a user to get API key
        user_data = {"email": f"test-{int(time.time())}@example.com"}
        async with http_client.post(
            f"{base_url}/auth/register",
            json=user_data
        ) as response:
            user_info = await response.json()
            api_key = user_info["api_key"]
        
        # Test job creation without callback
        job_data = {
            "task_type": "data_process",
            "payload": {"file_id": "12345", "format": "csv"}
        }
        
        headers = {"X-API-Key": api_key}
        async with http_client.post(
            f"{base_url}/api/jobs",
            json=job_data,
            headers=headers
        ) as response:
            assert response.status == 202
            data = await response.json()
            assert "job_id" in data
            assert data["status"] == "queued"
    
    async def test_create_job_invalid_task_type(self, http_client, base_url):
        """Test creating job with empty task_type"""
        # First register a user to get API key
        user_data = {"email": f"test-{int(time.time())}@example.com"}
        async with http_client.post(
            f"{base_url}/auth/register",
            json=user_data
        ) as response:
            user_info = await response.json()
            api_key = user_info["api_key"]
        
        # Test job creation with invalid task_type
        job_data = {
            "task_type": "",
            "payload": {"test": "data"}
        }
        
        headers = {"X-API-Key": api_key}
        async with http_client.post(
            f"{base_url}/api/jobs",
            json=job_data,
            headers=headers
        ) as response:
            assert response.status == 422
            data = await response.json()
            assert "task_type cannot be empty" in str(data)
    
    async def test_create_job_invalid_callback_url(self, http_client, base_url):
        """Test creating job with invalid callback URL"""
        # First register a user to get API key
        user_data = {"email": f"test-{int(time.time())}@example.com"}
        async with http_client.post(
            f"{base_url}/auth/register",
            json=user_data
        ) as response:
            user_info = await response.json()
            api_key = user_info["api_key"]
        
        # Test job creation with invalid callback URL
        job_data = {
            "task_type": "test",
            "payload": {"test": "data"},
            "callback_url": "invalid-url"
        }
        
        headers = {"X-API-Key": api_key}
        async with http_client.post(
            f"{base_url}/api/jobs",
            json=job_data,
            headers=headers
        ) as response:
            assert response.status == 422
            data = await response.json()
            assert "valid URL" in str(data)
    
    async def test_create_job_unauthenticated(self, http_client, base_url):
        """Test creating job without authentication"""
        job_data = {
            "task_type": "test",
            "payload": {"test": "data"}
        }
        
        async with http_client.post(
            f"{base_url}/api/jobs",
            json=job_data
        ) as response:
            assert response.status == 401
            data = await response.json()
            assert "API key required" in data["detail"]
    
    async def test_create_job_missing_payload(self, http_client, base_url):
        """Test creating job with missing payload"""
        # First register a user to get API key
        user_data = {"email": f"test-{int(time.time())}@example.com"}
        async with http_client.post(
            f"{base_url}/auth/register",
            json=user_data
        ) as response:
            user_info = await response.json()
            api_key = user_info["api_key"]
        
        # Test job creation with missing payload
        job_data = {
            "task_type": "test"
            # Missing payload
        }
        
        headers = {"X-API-Key": api_key}
        async with http_client.post(
            f"{base_url}/api/jobs",
            json=job_data,
            headers=headers
        ) as response:
            assert response.status == 422
            data = await response.json()
            assert "payload" in str(data)
    
    async def test_create_job_complex_payload(self, http_client, base_url):
        """Test creating job with complex payload structure"""
        # First register a user to get API key
        user_data = {"email": f"test-{int(time.time())}@example.com"}
        async with http_client.post(
            f"{base_url}/auth/register",
            json=user_data
        ) as response:
            user_info = await response.json()
            api_key = user_info["api_key"]
        
        # Test job creation with complex payload
        job_data = {
            "task_type": "complex_task",
            "payload": {
                "nested": {
                    "level1": {
                        "level2": ["item1", "item2", {"key": "value"}]
                    }
                },
                "numbers": [1, 2, 3, 4, 5],
                "boolean": True,
                "null_value": None
            }
        }
        
        headers = {"X-API-Key": api_key}
        async with http_client.post(
            f"{base_url}/api/jobs",
            json=job_data,
            headers=headers
        ) as response:
            assert response.status == 202
            data = await response.json()
            assert "job_id" in data
            assert data["status"] == "queued"
