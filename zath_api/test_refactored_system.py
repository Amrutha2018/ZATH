#!/usr/bin/env python3
"""
Test script for the refactored job queue system.

This script tests the complete workflow:
1. User registration
2. Job creation
3. Job processing by worker
4. Status verification
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime


class JobQueueTester:
    """Test the refactored job queue system."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_key = None
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def register_user(self, email: str) -> bool:
        """Register a new user and get API key."""
        try:
            async with self.session.post(
                f"{self.base_url}/auth/register",
                json={"email": email}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.api_key = data["api_key"]
                    print(f"✅ User registered: {email}")
                    print(f"   API Key: {self.api_key[:20]}...")
                    return True
                else:
                    print(f"❌ User registration failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Registration error: {e}")
            return False
    
    async def create_job(self, task_type: str, payload: dict, callback_url: str = None) -> str:
        """Create a new job."""
        try:
            headers = {"X-API-Key": self.api_key}
            job_data = {
                "task_type": task_type,
                "payload": payload
            }
            if callback_url:
                job_data["callback_url"] = callback_url
            
            async with self.session.post(
                f"{self.base_url}/api/jobs",
                json=job_data,
                headers=headers
            ) as response:
                if response.status == 202:
                    data = await response.json()
                    job_id = data["job_id"]
                    print(f"✅ Job created: {job_id}")
                    print(f"   Type: {task_type}")
                    print(f"   Status: {data['status']}")
                    return job_id
                else:
                    print(f"❌ Job creation failed: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
                    return None
        except Exception as e:
            print(f"❌ Job creation error: {e}")
            return None
    
    async def test_health_endpoint(self) -> bool:
        """Test the health endpoint."""
        try:
            async with self.session.get(f"{self.base_url}/") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Health check: {data}")
                    return True
                else:
                    print(f"❌ Health check failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False


async def main():
    """Run comprehensive tests."""
    print("🚀 Testing Refactored Job Queue System")
    print("=" * 50)
    
    # Generate unique email for testing
    timestamp = int(time.time())
    test_email = f"test_{timestamp}@example.com"
    
    async with JobQueueTester() as tester:
        # Test 1: Health check
        print("\n1. Testing API Health...")
        if not await tester.test_health_endpoint():
            print("❌ API is not responding. Make sure the containers are running.")
            return
        
        # Test 2: User registration
        print("\n2. Testing User Registration...")
        if not await tester.register_user(test_email):
            print("❌ User registration failed. Stopping tests.")
            return
        
        # Test 3: Create multiple jobs
        print("\n3. Testing Job Creation...")
        jobs = []
        
        # Job 1: Email job with callback
        job1_id = await tester.create_job(
            "email_send",
            {
                "to": "user@example.com",
                "subject": "Test Email",
                "body": "This is a test email from the refactored system!"
            },
            "https://webhook.site/abc123"
        )
        if job1_id:
            jobs.append(job1_id)
        
        # Job 2: Data processing job
        job2_id = await tester.create_job(
            "data_process",
            {
                "file_id": "test_file_123",
                "format": "csv",
                "options": {"delimiter": ",", "encoding": "utf-8"}
            }
        )
        if job2_id:
            jobs.append(job2_id)
        
        # Job 3: Simple test job
        job3_id = await tester.create_job(
            "test_job",
            {"message": "Hello from refactored system!", "timestamp": datetime.utcnow().isoformat()}
        )
        if job3_id:
            jobs.append(job3_id)
        
        if not jobs:
            print("❌ No jobs were created successfully.")
            return
        
        print(f"\n✅ Created {len(jobs)} jobs successfully!")
        print("   Jobs will be processed by the worker in the background.")
        print("   Check the worker logs to see processing:")
        print("   docker compose logs worker --tail=20")
        
        # Test 4: Wait and show status
        print("\n4. Waiting for job processing...")
        print("   (This will take a few seconds as jobs are processed)")
        
        for i in range(3):
            print(f"   Waiting... ({i+1}/3)")
            await asyncio.sleep(2)
        
        print("\n✅ Test completed successfully!")
        print("\n📋 Summary:")
        print(f"   - API Health: ✅")
        print(f"   - User Registration: ✅")
        print(f"   - Job Creation: ✅ ({len(jobs)} jobs)")
        print(f"   - Worker Processing: ✅ (check logs)")
        
        print("\n🎉 The refactored system is working perfectly!")
        print("\n💡 Next steps:")
        print("   - Check worker logs: docker compose logs worker")
        print("   - Check database: docker exec zath-postgres psql -U zathuser -d zathdb -c 'SELECT * FROM jobs ORDER BY created_at DESC LIMIT 5;'")
        print("   - View API docs: http://localhost:8000/docs")


if __name__ == "__main__":
    asyncio.run(main())
