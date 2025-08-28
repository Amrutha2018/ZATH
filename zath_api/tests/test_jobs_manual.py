#!/usr/bin/env python3
"""
Manual test script for Jobs API

This script tests the /api/jobs endpoint functionality.
For comprehensive API documentation, visit http://localhost:8000/docs
"""
import asyncio
import aiohttp
import json
import time

BASE_URL = "http://localhost:8000"

async def test_jobs_api():
    """Test the jobs API manually"""
    print("🧪 Testing Jobs API...")
    
    async with aiohttp.ClientSession() as session:
        # 1. Register a user
        print("\n1. Registering user...")
        user_data = {"email": f"jobs-test-{int(time.time())}@example.com"}
        async with session.post(f"{BASE_URL}/auth/register", json=user_data) as response:
            user_info = await response.json()
            api_key = user_info["api_key"]
            print(f"   ✅ User registered, API key: {api_key[:20]}...")
        
        # 2. Test valid job creation
        print("\n2. Testing valid job creation...")
        job_data = {
            "task_type": "email_send",
            "payload": {"to": "user@example.com", "subject": "Hello World"},
            "callback_url": "https://webhook.site/abc123"
        }
        headers = {"X-API-Key": api_key}
        async with session.post(f"{BASE_URL}/api/jobs", json=job_data, headers=headers) as response:
            if response.status == 202:
                result = await response.json()
                print(f"   ✅ Job created: {result['job_id']}")
            else:
                print(f"   ❌ Failed: {response.status}")
        
        # 3. Test job without callback
        print("\n3. Testing job without callback...")
        job_data = {
            "task_type": "data_process",
            "payload": {"file_id": "12345", "format": "csv"}
        }
        async with session.post(f"{BASE_URL}/api/jobs", json=job_data, headers=headers) as response:
            if response.status == 202:
                result = await response.json()
                print(f"   ✅ Job created: {result['job_id']}")
            else:
                print(f"   ❌ Failed: {response.status}")
        
        # 4. Test invalid task_type
        print("\n4. Testing invalid task_type...")
        job_data = {
            "task_type": "",
            "payload": {"test": "data"}
        }
        async with session.post(f"{BASE_URL}/api/jobs", json=job_data, headers=headers) as response:
            if response.status == 422:
                print("   ✅ Correctly rejected empty task_type")
            else:
                print(f"   ❌ Unexpected response: {response.status}")
        
        # 5. Test invalid callback URL
        print("\n5. Testing invalid callback URL...")
        job_data = {
            "task_type": "test",
            "payload": {"test": "data"},
            "callback_url": "invalid-url"
        }
        async with session.post(f"{BASE_URL}/api/jobs", json=job_data, headers=headers) as response:
            if response.status == 422:
                print("   ✅ Correctly rejected invalid URL")
            else:
                print(f"   ❌ Unexpected response: {response.status}")
        
        # 6. Test unauthenticated request
        print("\n6. Testing unauthenticated request...")
        job_data = {
            "task_type": "test",
            "payload": {"test": "data"}
        }
        async with session.post(f"{BASE_URL}/api/jobs", json=job_data) as response:
            if response.status == 401:
                print("   ✅ Correctly rejected unauthenticated request")
            else:
                print(f"   ❌ Unexpected response: {response.status}")
        
        print("\n🎉 Jobs API testing completed!")

if __name__ == "__main__":
    asyncio.run(test_jobs_api())
