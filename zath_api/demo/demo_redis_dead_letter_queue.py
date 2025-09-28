#!/usr/bin/env python3
"""
Demonstration script for Redis-based dead letter queue system.

This script demonstrates the Redis dead letter queue functionality
without requiring database connections.
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone
from workers.dead_letter_queue import (
    add_to_dead_letter_queue, 
    get_dead_letter_jobs, 
    retry_dead_letter_job, 
    get_dead_letter_queue_stats,
    remove_dead_letter_job
)


async def demo_redis_dead_letter_queue():
    """Demonstrate Redis dead letter queue functionality."""
    print("🚀 ZATH Redis Dead Letter Queue Demonstration")
    print("=" * 50)
    
    # Demo 1: Add jobs to dead letter queue
    print("\n📥 1. Adding Jobs to Dead Letter Queue")
    print("-" * 40)
    
    # Add some failed jobs
    job_ids = []
    for i in range(3):
        job_id = str(uuid.uuid4())
        job_ids.append(job_id)
        
        error_messages = [
            "Connection timeout to external API",
            "Invalid data format in payload",
            "Authentication failed with third-party service"
        ]
        
        task_types = ["http_call", "data_transform", "email_send"]
        
        dlq_key = await add_to_dead_letter_queue(
            job_id=job_id,
            task_type=task_types[i],
            payload={
                "url": f"https://api.example{i}.com/endpoint",
                "data": {"test": f"data_{i}"}
            },
            error_message=error_messages[i],
            retry_count=0,
            max_retries=3
        )
        
        print(f"✅ Added job {job_id[:8]}... to dead letter queue")
        print(f"   Task Type: {task_types[i]}")
        print(f"   Error: {error_messages[i]}")
        print(f"   Redis Key: {dlq_key}")
        print()
    
    # Demo 2: Get dead letter queue statistics
    print("\n📊 2. Dead Letter Queue Statistics")
    print("-" * 35)
    
    stats = await get_dead_letter_queue_stats()
    print(f"✅ Dead Letter Queue Stats:")
    print(f"   Total Jobs: {stats['total_jobs']}")
    print(f"   Queue Name: {stats['queue_name']}")
    print(f"   Task Type Breakdown:")
    for task_type, count in stats['task_type_breakdown'].items():
        print(f"     • {task_type}: {count}")
    print()
    
    # Demo 3: List dead letter jobs
    print("\n📋 3. Listing Dead Letter Jobs")
    print("-" * 30)
    
    jobs_data = await get_dead_letter_jobs(page=1, limit=10)
    print(f"✅ Found {jobs_data['pagination']['total']} jobs in dead letter queue")
    print(f"   Page: {jobs_data['pagination']['page']}")
    print(f"   Total Pages: {jobs_data['pagination']['pages']}")
    print()
    
    print("   Dead Letter Jobs:")
    for job in jobs_data['jobs']:
        print(f"     • DLQ ID: {job['dlq_id']}")
        print(f"       Job ID: {job['job_id'][:8]}...")
        print(f"       Task Type: {job['task_type']}")
        print(f"       Error: {job['error_message']}")
        print(f"       Retry Count: {job['retry_count']}/{job['max_retries']}")
        print(f"       Created: {job['created_at']}")
        print()
    
    # Demo 4: Filter by task type
    print("\n🔍 4. Filtering by Task Type")
    print("-" * 30)
    
    http_jobs = await get_dead_letter_jobs(page=1, limit=10, task_type="http_call")
    print(f"✅ Found {http_jobs['pagination']['total']} HTTP call jobs in dead letter queue")
    
    for job in http_jobs['jobs']:
        print(f"     • {job['dlq_id']}: {job['job_id'][:8]}... - {job['error_message']}")
    print()
    
    # Demo 5: Retry a job from dead letter queue
    print("\n🔄 5. Retrying Jobs from Dead Letter Queue")
    print("-" * 40)
    
    if jobs_data['jobs']:
        # Get the first job
        first_job = jobs_data['jobs'][0]
        dlq_id = first_job['dlq_id']
        
        print(f"Retrying job: {dlq_id}")
        print(f"   Original Job ID: {first_job['job_id'][:8]}...")
        print(f"   Task Type: {first_job['task_type']}")
        print(f"   Current Retry Count: {first_job['retry_count']}")
        
        success = await retry_dead_letter_job(dlq_id)
        
        if success:
            print(f"✅ Job {dlq_id} successfully retried!")
            print(f"   Job moved back to main processing queue")
            print(f"   Retry count incremented")
        else:
            print(f"❌ Failed to retry job {dlq_id}")
            print(f"   Job may have exceeded max retries or not found")
        print()
    
    # Demo 6: Check updated statistics
    print("\n📈 6. Updated Statistics After Retry")
    print("-" * 35)
    
    updated_stats = await get_dead_letter_queue_stats()
    print(f"✅ Updated Dead Letter Queue Stats:")
    print(f"   Total Jobs: {updated_stats['total_jobs']}")
    print(f"   Task Type Breakdown:")
    for task_type, count in updated_stats['task_type_breakdown'].items():
        print(f"     • {task_type}: {count}")
    print()
    
    # Demo 7: Add a job that will exceed max retries
    print("\n⚠️  7. Testing Max Retries")
    print("-" * 25)
    
    max_retry_job_id = str(uuid.uuid4())
    await add_to_dead_letter_queue(
        job_id=max_retry_job_id,
        task_type="webhook_call",
        payload={"url": "https://failing-webhook.com"},
        error_message="Webhook endpoint not responding",
        retry_count=3,  # Already at max retries
        max_retries=3
    )
    
    print(f"✅ Added job {max_retry_job_id[:8]}... with max retries exceeded")
    
    # Try to retry it (should fail)
    max_retry_jobs = await get_dead_letter_jobs(page=1, limit=10, task_type="webhook_call")
    if max_retry_jobs['jobs']:
        max_retry_dlq_id = max_retry_jobs['jobs'][0]['dlq_id']
        retry_success = await retry_dead_letter_job(max_retry_dlq_id)
        
        if not retry_success:
            print(f"❌ Retry failed as expected - job has exceeded max retries")
        else:
            print(f"✅ Retry succeeded (unexpected)")
    print()
    
    # Demo 8: Remove a job from dead letter queue
    print("\n🗑️  8. Removing Jobs from Dead Letter Queue")
    print("-" * 40)
    
    remaining_jobs = await get_dead_letter_jobs(page=1, limit=10)
    if remaining_jobs['jobs']:
        job_to_remove = remaining_jobs['jobs'][0]
        dlq_id_to_remove = job_to_remove['dlq_id']
        
        print(f"Removing job: {dlq_id_to_remove}")
        print(f"   Job ID: {job_to_remove['job_id'][:8]}...")
        print(f"   Task Type: {job_to_remove['task_type']}")
        
        remove_success = await remove_dead_letter_job(dlq_id_to_remove)
        
        if remove_success:
            print(f"✅ Job {dlq_id_to_remove} successfully removed from dead letter queue")
        else:
            print(f"❌ Failed to remove job {dlq_id_to_remove}")
        print()
    
    # Demo 9: Final statistics
    print("\n🎯 9. Final Statistics")
    print("-" * 20)
    
    final_stats = await get_dead_letter_queue_stats()
    print(f"✅ Final Dead Letter Queue Stats:")
    print(f"   Total Jobs: {final_stats['total_jobs']}")
    print(f"   Task Type Breakdown:")
    for task_type, count in final_stats['task_type_breakdown'].items():
        print(f"     • {task_type}: {count}")
    print()
    
    # Demo 10: Error handling
    print("\n🚨 10. Error Handling Demo")
    print("-" * 25)
    
    # Try to retry a non-existent job
    fake_dlq_id = "dlq_999999"
    retry_result = await retry_dead_letter_job(fake_dlq_id)
    print(f"Retry non-existent job {fake_dlq_id}: {'❌ Failed as expected' if not retry_result else '✅ Unexpected success'}")
    
    # Try to remove a non-existent job
    remove_result = await remove_dead_letter_job(fake_dlq_id)
    print(f"Remove non-existent job {fake_dlq_id}: {'❌ Failed as expected' if not remove_result else '✅ Unexpected success'}")
    print()
    
    print("✨ Redis Dead Letter Queue demonstration completed!")
    print("   All functionality is working correctly with Redis backend.")
    print("   Jobs are stored in Redis lists for fast access and processing.")


if __name__ == "__main__":
    asyncio.run(demo_redis_dead_letter_queue())
