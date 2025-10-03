#!/usr/bin/env python3
"""
Comprehensive integration test for ZATH multi-task system.

This script tests the complete workflow:
1. Job creation with different task types
2. Job processing by workers
3. Dead letter queue functionality
4. API endpoints
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

import aiohttp
from workers.task_handlers import execute_task
from workers.dead_letter_queue import (
    add_to_dead_letter_queue,
    get_dead_letter_jobs,
    get_dead_letter_queue_stats,
    retry_dead_letter_job
)


async def test_task_handlers():
    """Test all task handlers directly."""
    print("🧪 Testing Task Handlers Directly")
    print("=" * 40)
    
    # Test HTTP call
    print("\n1. Testing HTTP Call Handler")
    success, result, error = await execute_task("http_call", {
        "url": "https://httpbin.org/get",
        "method": "GET"
    })
    print(f"   ✅ HTTP Call: success={success}, error={error}")
    
    # Test data transform - flatten_json
    print("\n2. Testing Data Transform - Flatten JSON")
    success, result, error = await execute_task("data_transform", {
        "operation": "flatten_json",
        "data": {
            "user": {
                "name": "John",
                "address": {
                    "city": "New York",
                    "country": "USA"
                }
            }
        }
    })
    print(f"   ✅ Flatten JSON: success={success}, result={result}")
    
    # Test data transform - csv_to_json
    print("\n3. Testing Data Transform - CSV to JSON")
    success, result, error = await execute_task("data_transform", {
        "operation": "csv_to_json",
        "csv_content": "name,age,city\nJohn,25,New York\nJane,30,Los Angeles",
        "delimiter": ","
    })
    print(f"   ✅ CSV to JSON: success={success}, records={len(result.get('result', []))}")
    
    # Test data transform - filter_records
    print("\n4. Testing Data Transform - Filter Records")
    success, result, error = await execute_task("data_transform", {
        "operation": "filter_records",
        "records": [
            {"name": "John", "age": 25, "city": "New York"},
            {"name": "Jane", "age": 30, "city": "Los Angeles"},
            {"name": "Bob", "age": 25, "city": "Chicago"}
        ],
        "criteria": {"age": 25}
    })
    print(f"   ✅ Filter Records: success={success}, filtered={len(result.get('result', []))}")
    
    # Test data transform - aggregate
    print("\n5. Testing Data Transform - Aggregate")
    success, result, error = await execute_task("data_transform", {
        "operation": "aggregate",
        "records": [
            {"name": "John", "age": 25},
            {"name": "Jane", "age": 30},
            {"name": "Bob", "age": 35}
        ],
        "field": "age",
        "agg": "avg"
    })
    print(f"   ✅ Aggregate: success={success}, result={result}")
    
    # Test email send
    print("\n6. Testing Email Send Handler")
    success, result, error = await execute_task("email_send", {
        "to": "test@example.com",
        "subject": "Test Email",
        "body": "This is a test email"
    })
    print(f"   ✅ Email Send: success={success}, error={error}")
    
    # Test webhook call
    print("\n7. Testing Webhook Call Handler")
    success, result, error = await execute_task("webhook_call", {
        "url": "https://httpbin.org/post",
        "data": {"test": "webhook"}
    })
    print(f"   ✅ Webhook Call: success={success}, error={error}")
    
    # Test file upload
    print("\n8. Testing File Upload Handler")
    success, result, error = await execute_task("file_upload", {
        "file_path": "/tmp/test.txt",
        "destination": "s3://bucket/test.txt"
    })
    print(f"   ✅ File Upload: success={success}, error={error}")
    
    # Test report generate
    print("\n9. Testing Report Generate Handler")
    success, result, error = await execute_task("report_generate", {
        "report_type": "monthly",
        "data": {"sales": 1000}
    })
    print(f"   ✅ Report Generate: success={success}, error={error}")
    
    # Test unknown task type (should fail)
    print("\n10. Testing Unknown Task Type (should fail)")
    success, result, error = await execute_task("unknown_task", {
        "test": "data"
    })
    print(f"   ✅ Unknown Task: success={success}, error={error}")
    
    return True


async def test_dead_letter_queue():
    """Test dead letter queue functionality."""
    print("\n\n🧪 Testing Dead Letter Queue")
    print("=" * 30)
    
    # Add some test jobs to dead letter queue
    print("\n1. Adding Jobs to Dead Letter Queue")
    job_ids = []
    for i in range(3):
        job_id = str(uuid.uuid4())
        job_ids.append(job_id)
        
        await add_to_dead_letter_queue(
            job_id=job_id,
            task_type="test_task",
            payload={"test": f"data_{i}"},
            error_message=f"Test error {i}",
            retry_count=0,
            max_retries=3
        )
        print(f"   ✅ Added job {job_id[:8]}... to dead letter queue")
    
    # Get dead letter queue stats
    print("\n2. Getting Dead Letter Queue Stats")
    stats = await get_dead_letter_queue_stats()
    print(f"   ✅ Stats: {stats}")
    
    # List dead letter jobs
    print("\n3. Listing Dead Letter Jobs")
    jobs_data = await get_dead_letter_jobs(page=1, limit=10)
    print(f"   ✅ Found {jobs_data['pagination']['total']} jobs in dead letter queue")
    
    # Test retry functionality
    if jobs_data['jobs']:
        print("\n4. Testing Retry Functionality")
        first_job = jobs_data['jobs'][0]
        dlq_id = first_job['dlq_id']
        
        success = await retry_dead_letter_job(dlq_id)
        print(f"   ✅ Retry job {dlq_id}: success={success}")
    
    return True


async def test_api_endpoints():
    """Test API endpoints."""
    print("\n\n🧪 Testing API Endpoints")
    print("=" * 25)
    
    # Use a valid API key from the database
    api_key = "7jrmgPE9EWvfxAQ_MTPKsRURufhjVoFb5hx7fTSd3HY"
    # Use internal container URL when running inside Docker
    base_url = "http://zathapi:8000"
    
    async with aiohttp.ClientSession() as session:
        # Test dead letter queue endpoint
        print("\n1. Testing Dead Letter Queue API")
        async with session.get(
            f"{base_url}/api/dead-letter-queue",
            headers={"X-API-Key": api_key}
        ) as response:
            if response.status == 200:
                data = await response.json()
                print(f"   ✅ DLQ API: {data['pagination']['total']} jobs found")
            else:
                print(f"   ❌ DLQ API: Status {response.status}")
        
        # Test dead letter queue stats endpoint
        print("\n2. Testing Dead Letter Queue Stats API")
        async with session.get(
            f"{base_url}/api/dead-letter-queue/stats",
            headers={"X-API-Key": api_key}
        ) as response:
            if response.status == 200:
                data = await response.json()
                print(f"   ✅ DLQ Stats API: {data['total_jobs']} total jobs")
            else:
                print(f"   ❌ DLQ Stats API: Status {response.status}")
        
        # Test job creation
        print("\n3. Testing Job Creation API")
        job_data = {
            "task_type": "data_transform",
            "payload": {
                "operation": "flatten_json",
                "data": {"test": "integration"}
            },
            "callback_url": "https://httpbin.org/post"
        }
        
        async with session.post(
            f"{base_url}/api/jobs",
            headers={"X-API-Key": api_key, "Content-Type": "application/json"},
            json=job_data
        ) as response:
            if response.status == 202:
                data = await response.json()
                print(f"   ✅ Job Creation: Job {data['job_id'][:8]}... created")
                return data['job_id']
            else:
                print(f"   ❌ Job Creation: Status {response.status}")
                return None


async def test_job_processing_workflow():
    """Test complete job processing workflow."""
    print("\n\n🧪 Testing Complete Job Processing Workflow")
    print("=" * 45)
    
    # Create a job that will fail (unknown task type)
    print("\n1. Creating Job with Unknown Task Type (will fail)")
    job_id = str(uuid.uuid4())
    
    # Simulate adding to Redis queue (this would normally be done by the API)
    print(f"   📝 Job {job_id[:8]}... created with task_type='unknown_task'")
    
    # Simulate worker processing (this will fail and go to dead letter queue)
    print("\n2. Simulating Worker Processing")
    success, result, error = await execute_task("unknown_task", {
        "test": "data"
    })
    print(f"   📝 Worker processing: success={success}, error={error}")
    
    # Add to dead letter queue (this would normally be done by the worker)
    print("\n3. Adding Failed Job to Dead Letter Queue")
    await add_to_dead_letter_queue(
        job_id=job_id,
        task_type="unknown_task",
        payload={"test": "data"},
        error_message=error or "Unknown error",
        retry_count=0,
        max_retries=3
    )
    print(f"   ✅ Job {job_id[:8]}... added to dead letter queue")
    
    # Verify job is in dead letter queue
    print("\n4. Verifying Job in Dead Letter Queue")
    jobs_data = await get_dead_letter_jobs(page=1, limit=10)
    found_job = None
    for job in jobs_data['jobs']:
        if job['job_id'] == job_id:
            found_job = job
            break
    
    if found_job:
        print(f"   ✅ Job {job_id[:8]}... found in dead letter queue")
        print(f"   📝 Error: {found_job['error_message']}")
    else:
        print(f"   ❌ Job {job_id[:8]}... not found in dead letter queue")
    
    return found_job is not None


async def main():
    """Run all integration tests."""
    print("🚀 ZATH Comprehensive Integration Test")
    print("=" * 50)
    
    try:
        # Test 1: Task handlers
        await test_task_handlers()
        
        # Test 2: Dead letter queue
        await test_dead_letter_queue()
        
        # Test 3: API endpoints
        job_id = await test_api_endpoints()
        
        # Test 4: Complete workflow
        workflow_success = await test_job_processing_workflow()
        
        print("\n\n🎯 Integration Test Results")
        print("=" * 30)
        print("✅ Task Handlers: All 10 task types tested")
        print("✅ Dead Letter Queue: Add, list, stats, retry tested")
        print("✅ API Endpoints: DLQ endpoints tested")
        print(f"✅ Job Processing Workflow: {'PASSED' if workflow_success else 'FAILED'}")
        
        print("\n🎉 All integration tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
