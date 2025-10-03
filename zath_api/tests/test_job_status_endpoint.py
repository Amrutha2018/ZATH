#!/usr/bin/env python3
"""
Test script for job status endpoint
Tests the new GET /api/jobs/{job_id} endpoint functionality
"""
import asyncio
import aiohttp
import json
import time
from datetime import datetime

class JobStatusTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_key = None
        self.test_job_id = None
    
    async def register_user(self):
        """Register a test user and get API key"""
        print("🔐 Registering test user...")
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/auth/register",
                headers={"Content-Type": "application/json"},
                json={"email": f"test_job_status_{int(time.time())}@example.com"}
            ) as response:
                if response.status == 200:
                    user_data = await response.json()
                    self.api_key = user_data["api_key"]
                    print(f"✅ User registered with API key: {self.api_key[:10]}...")
                    return True
                else:
                    print(f"❌ Failed to register user: {response.status}")
                    return False
    
    async def create_test_job(self):
        """Create a test job for status checking"""
        print("📝 Creating test job...")
        test_job_data = {
            "task_type": "test_job_status",
            "payload": {
                "test": "data",
                "timestamp": datetime.utcnow().isoformat(),
                "message": "This is a test job for status endpoint"
            },
            "callback_url": "https://webhook.site/test-status"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/jobs",
                headers={
                    "X-API-Key": self.api_key,
                    "Content-Type": "application/json"
                },
                json=test_job_data
            ) as response:
                if response.status == 202:
                    job_response = await response.json()
                    self.test_job_id = job_response["job_id"]
                    print(f"✅ Test job created with ID: {self.test_job_id}")
                    return True
                else:
                    print(f"❌ Failed to create test job: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
                    return False
    
    async def test_valid_job_status(self):
        """Test retrieving status of a valid job"""
        print(f"\n🔍 Testing valid job status retrieval for {self.test_job_id}...")
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/api/jobs/{self.test_job_id}",
                headers={"X-API-Key": self.api_key}
            ) as response:
                if response.status == 200:
                    job_status = await response.json()
                    print(f"✅ Job status retrieved successfully!")
                    print(f"   Job ID: {job_status['job_id']}")
                    print(f"   Task Type: {job_status['task_type']}")
                    print(f"   Status: {job_status['status']}")
                    print(f"   Created At: {job_status['created_at']}")
                    print(f"   Retry Count: {job_status['retry_count']}")
                    print(f"   Has Payload: {'Yes' if job_status['payload'] else 'No'}")
                    print(f"   Has Callback URL: {'Yes' if job_status['callback_url'] else 'No'}")
                    return True
                else:
                    print(f"❌ Failed to get job status: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
                    return False
    
    async def test_invalid_uuid_format(self):
        """Test with invalid UUID format"""
        print(f"\n🚫 Testing invalid UUID format...")
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/api/jobs/invalid-uuid-format",
                headers={"X-API-Key": self.api_key}
            ) as response:
                if response.status == 422:
                    error_data = await response.json()
                    print(f"✅ Correctly rejected invalid UUID format")
                    print(f"   Error: {error_data['detail']}")
                    return True
                else:
                    print(f"❌ Expected 422, got {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
                    return False
    
    async def test_nonexistent_job(self):
        """Test with non-existent job ID"""
        print(f"\n🔍 Testing non-existent job ID...")
        fake_job_id = "123e4567-e89b-12d3-a456-426614174999"
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/api/jobs/{fake_job_id}",
                headers={"X-API-Key": self.api_key}
            ) as response:
                if response.status == 404:
                    error_data = await response.json()
                    print(f"✅ Correctly returned 404 for non-existent job")
                    print(f"   Error: {error_data['detail']}")
                    return True
                else:
                    print(f"❌ Expected 404, got {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
                    return False
    
    async def test_without_authentication(self):
        """Test without API key authentication"""
        print(f"\n🔐 Testing without authentication...")
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/api/jobs/{self.test_job_id}") as response:
                if response.status == 401:
                    error_data = await response.json()
                    print(f"✅ Correctly required authentication")
                    print(f"   Error: {error_data['detail']}")
                    return True
                else:
                    print(f"❌ Expected 401, got {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
                    return False
    
    async def test_empty_job_id(self):
        """Test with empty job ID"""
        print(f"\n🚫 Testing empty job ID...")
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/api/jobs/",
                headers={"X-API-Key": self.api_key}
            ) as response:
                if response.status == 405:  # FastAPI returns 405 Method Not Allowed for /api/jobs/ without job_id
                    print(f"✅ Correctly handled empty job ID (405 Method Not Allowed)")
                    return True
                else:
                    print(f"❌ Expected 405, got {response.status}")
                    return False
    
    async def test_different_status_values(self):
        """Test jobs with different status values (if available)"""
        print(f"\n📊 Testing different job status values...")
        # This would require creating jobs and having the worker process them
        # For now, we'll just check what status our test job has
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/api/jobs/{self.test_job_id}",
                headers={"X-API-Key": self.api_key}
            ) as response:
                if response.status == 200:
                    job_status = await response.json()
                    status = job_status['status']
                    print(f"✅ Current job status: {status}")
                    print(f"   Expected status values: queued, in_progress, completed, failed")
                    return True
                else:
                    print(f"❌ Failed to get job status for status testing: {response.status}")
                    return False

async def main():
    """Main test function"""
    print("🚀 Starting Job Status Endpoint Tests")
    print("=" * 50)
    
    tester = JobStatusTester()
    
    # Test flow
    tests = [
        ("User Registration", tester.register_user),
        ("Create Test Job", tester.create_test_job),
        ("Valid Job Status", tester.test_valid_job_status),
        ("Invalid UUID Format", tester.test_invalid_uuid_format),
        ("Non-existent Job", tester.test_nonexistent_job),
        ("Without Authentication", tester.test_without_authentication),
        ("Empty Job ID", tester.test_empty_job_id),
        ("Different Status Values", tester.test_different_status_values),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if await test_func():
                passed += 1
        except Exception as e:
            print(f"❌ Test '{test_name}' failed with exception: {str(e)}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Job status endpoint is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
