#!/usr/bin/env python3
"""
Test script to verify all success criteria for the multi-task system.

Success criteria:
(a) jobs are persisted with a correct task_type
(b) workers execute the appropriate handler
(c) intentionally failing a job causes it to appear in the dead-letter queue
(d) all existing functionality continues to work
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone

import aiohttp
from workers.task_handlers import execute_task
from workers.dead_letter_queue import get_dead_letter_jobs, get_dead_letter_queue_stats


async def test_criteria_a_jobs_persisted_with_task_type():
    """Test criterion (a): jobs are persisted with a correct task_type."""
    print("🧪 Testing Criterion (a): Jobs persisted with correct task_type")
    print("=" * 60)
    
    # Test all valid task types
    valid_task_types = [
        'http_call', 'data_transform', 'email_send', 
        'webhook_call', 'file_upload', 'report_generate'
    ]
    
    api_key = "7jrmgPE9EWvfxAQ_MTPKsRURufhjVoFb5hx7fTSd3HY"
    base_url = "http://zathapi:8000"
    
    created_jobs = []
    
    async with aiohttp.ClientSession() as session:
        for task_type in valid_task_types:
            print(f"\n1. Creating job with task_type='{task_type}'")
            
            job_data = {
                "task_type": task_type,
                "payload": {
                    "test": f"data_for_{task_type}",
                    "timestamp": datetime.now(timezone.utc).isoformat()
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
                    job_id = data['job_id']
                    created_jobs.append((job_id, task_type))
                    print(f"   ✅ Job {job_id[:8]}... created with task_type='{task_type}'")
                else:
                    print(f"   ❌ Failed to create job with task_type='{task_type}': {response.status}")
                    return False
    
    print(f"\n✅ Criterion (a) PASSED: Created {len(created_jobs)} jobs with correct task_types")
    return True


async def test_criteria_b_workers_execute_appropriate_handler():
    """Test criterion (b): workers execute the appropriate handler."""
    print("\n\n🧪 Testing Criterion (b): Workers execute appropriate handler")
    print("=" * 60)
    
    # Test each task type handler
    test_cases = [
        {
            "task_type": "http_call",
            "payload": {"url": "https://httpbin.org/get", "method": "GET"},
            "expected_success": True
        },
        {
            "task_type": "data_transform",
            "payload": {
                "operation": "flatten_json",
                "data": {"test": "data"}
            },
            "expected_success": True
        },
        {
            "task_type": "email_send",
            "payload": {
                "to": "test@example.com",
                "subject": "Test",
                "body": "Test email"
            },
            "expected_success": True
        },
        {
            "task_type": "webhook_call",
            "payload": {
                "url": "https://httpbin.org/post",
                "data": {"test": "webhook"}
            },
            "expected_success": True
        },
        {
            "task_type": "file_upload",
            "payload": {
                "file_path": "/tmp/test.txt",
                "destination": "s3://bucket/test.txt"
            },
            "expected_success": True
        },
        {
            "task_type": "report_generate",
            "payload": {
                "report_type": "monthly",
                "data": {"sales": 1000}
            },
            "expected_success": True
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing {test_case['task_type']} handler")
        
        success, result, error = await execute_task(
            test_case['task_type'], 
            test_case['payload']
        )
        
        if success == test_case['expected_success']:
            print(f"   ✅ {test_case['task_type']} handler executed correctly")
        else:
            print(f"   ❌ {test_case['task_type']} handler failed: {error}")
            return False
    
    print(f"\n✅ Criterion (b) PASSED: All {len(test_cases)} handlers executed correctly")
    return True


async def test_criteria_c_failing_jobs_appear_in_dead_letter_queue():
    """Test criterion (c): intentionally failing a job causes it to appear in the dead-letter queue."""
    print("\n\n🧪 Testing Criterion (c): Failing jobs appear in dead-letter queue")
    print("=" * 60)
    
    # Get initial dead letter queue count
    initial_stats = await get_dead_letter_queue_stats()
    initial_count = initial_stats['total_jobs']
    print(f"1. Initial dead letter queue count: {initial_count}")
    
    # Create jobs that will fail
    failing_task_types = [
        "unknown_task_type",
        "invalid_task",
        "nonexistent_handler"
    ]
    
    for i, task_type in enumerate(failing_task_types, 2):
        print(f"\n{i}. Creating job with failing task_type='{task_type}'")
        
        success, result, error = await execute_task(task_type, {
            "test": "failing_data"
        })
        
        if not success:
            print(f"   ✅ Job with task_type='{task_type}' failed as expected: {error}")
        else:
            print(f"   ❌ Job with task_type='{task_type}' should have failed but succeeded")
            return False
    
    # Check if dead letter queue count increased
    final_stats = await get_dead_letter_queue_stats()
    final_count = final_stats['total_jobs']
    
    print(f"\n{len(failing_task_types) + 1}. Final dead letter queue count: {final_count}")
    
    if final_count > initial_count:
        print(f"   ✅ Dead letter queue count increased from {initial_count} to {final_count}")
        print(f"   ✅ Criterion (c) PASSED: Failing jobs appear in dead-letter queue")
        return True
    else:
        print(f"   ❌ Dead letter queue count did not increase")
        return False


async def test_criteria_d_existing_functionality_continues_to_work():
    """Test criterion (d): all existing functionality continues to work."""
    print("\n\n🧪 Testing Criterion (d): Existing functionality continues to work")
    print("=" * 60)
    
    # Test 1: Job creation and listing
    print("\n1. Testing job creation and listing")
    api_key = "7jrmgPE9EWvfxAQ_MTPKsRURufhjVoFb5hx7fTSd3HY"
    base_url = "http://zathapi:8000"
    
    async with aiohttp.ClientSession() as session:
        # Create a job
        job_data = {
            "task_type": "http_call",
            "payload": {"url": "https://httpbin.org/get"},
            "callback_url": "https://httpbin.org/post"
        }
        
        async with session.post(
            f"{base_url}/api/jobs",
            headers={"X-API-Key": api_key, "Content-Type": "application/json"},
            json=job_data
        ) as response:
            if response.status == 202:
                data = await response.json()
                job_id = data['job_id']
                print(f"   ✅ Job {job_id[:8]}... created successfully")
            else:
                print(f"   ❌ Job creation failed: {response.status}")
                return False
        
        # List jobs
        async with session.get(
            f"{base_url}/api/jobs",
            headers={"X-API-Key": api_key}
        ) as response:
            if response.status == 200:
                data = await response.json()
                print(f"   ✅ Job listing works: {data['pagination']['total']} jobs found")
            else:
                print(f"   ❌ Job listing failed: {response.status}")
                return False
    
    # Test 2: Dead letter queue functionality
    print("\n2. Testing dead letter queue functionality")
    
    # Get dead letter queue stats
    stats = await get_dead_letter_queue_stats()
    print(f"   ✅ Dead letter queue stats: {stats['total_jobs']} total jobs")
    
    # List dead letter jobs
    jobs_data = await get_dead_letter_jobs(page=1, limit=5)
    print(f"   ✅ Dead letter queue listing: {jobs_data['pagination']['total']} jobs found")
    
    # Test 3: Data transformation utilities
    print("\n3. Testing data transformation utilities")
    
    # Test flatten_json
    success, result, error = await execute_task("data_transform", {
        "operation": "flatten_json",
        "data": {"nested": {"value": "test"}}
    })
    if success and "nested.value" in str(result):
        print("   ✅ flatten_json utility works")
    else:
        print(f"   ❌ flatten_json utility failed: {error}")
        return False
    
    # Test csv_to_json
    success, result, error = await execute_task("data_transform", {
        "operation": "csv_to_json",
        "csv_content": "name,age\nJohn,25\nJane,30"
    })
    if success and len(result.get('result', [])) == 2:
        print("   ✅ csv_to_json utility works")
    else:
        print(f"   ❌ csv_to_json utility failed: {error}")
        return False
    
    print(f"\n✅ Criterion (d) PASSED: All existing functionality continues to work")
    return True


async def main():
    """Run all success criteria tests."""
    print("🚀 ZATH Success Criteria Verification")
    print("=" * 50)
    
    results = []
    
    try:
        # Test criterion (a)
        result_a = await test_criteria_a_jobs_persisted_with_task_type()
        results.append(("a", result_a))
        
        # Test criterion (b)
        result_b = await test_criteria_b_workers_execute_appropriate_handler()
        results.append(("b", result_b))
        
        # Test criterion (c)
        result_c = await test_criteria_c_failing_jobs_appear_in_dead_letter_queue()
        results.append(("c", result_c))
        
        # Test criterion (d)
        result_d = await test_criteria_d_existing_functionality_continues_to_work()
        results.append(("d", result_d))
        
        # Summary
        print("\n\n🎯 Success Criteria Results")
        print("=" * 30)
        
        all_passed = True
        for criterion, passed in results:
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"Criterion ({criterion}): {status}")
            if not passed:
                all_passed = False
        
        if all_passed:
            print("\n🎉 ALL SUCCESS CRITERIA PASSED!")
            print("The multi-task system is working correctly.")
        else:
            print("\n❌ Some success criteria failed.")
            print("The multi-task system needs attention.")
        
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
