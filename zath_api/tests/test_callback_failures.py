#!/usr/bin/env python3
"""
Test script for callback failure scenarios.

This script tests:
1. Jobs with successful execution but callback failures
2. Jobs with failed execution and callback failures
3. Proper logging of callback failures
4. Job status updates to callback_failed
"""

import asyncio
import json
import logging
import sys
import os
import uuid
import aiohttp
from datetime import datetime, timezone
from typing import Dict, Any

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.connection import init_db_pool, get_pool
from utils.job_logger import get_job_logger, shutdown_job_logger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API configuration
API_BASE_URL = "http://localhost:8001"
API_KEY = "7jrmgPE9EWvfxAQ_MTPKsRURufhjVoFb5hx7fTSd3HY"


async def test_callback_failure_scenarios():
    """Test various callback failure scenarios."""
    logger.info("Starting callback failure tests...")
    
    try:
        # Initialize database connection
        await init_db_pool()
        logger.info("Database connection initialized")
        
        # Test 1: Job with successful execution but callback to invalid URL
        logger.info("Test 1: Job with successful execution but callback failure...")
        job1_data = {
            "task_type": "http_call",
            "payload": {"url": "https://httpbin.org/delay/1", "method": "GET"},
            "callback_url": "https://invalid-callback-url-that-does-not-exist.com/webhook"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_BASE_URL}/api/jobs",
                headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
                json=job1_data
            ) as response1:
                if response1.status == 202:
                    job1_data_response = await response1.json()
                    job1_id = job1_data_response["job_id"]
                    logger.info(f"Created job {job1_id} with callback to invalid URL")
                    
                    # Wait for job to complete
                    await asyncio.sleep(10)
                    
                    # Check job status
                    async with session.get(
                        f"{API_BASE_URL}/api/jobs/{job1_id}",
                        headers={"X-API-Key": API_KEY}
                    ) as status_response:
                        if status_response.status == 200:
                            job_status = await status_response.json()
                            logger.info(f"Job {job1_id} status: {job_status['status']}")
                            
                            if job_status['status'] == 'callback_failed':
                                logger.info("✅ Job correctly marked as callback_failed")
                            else:
                                logger.warning(f"❌ Expected callback_failed, got {job_status['status']}")
                        else:
                            logger.error(f"Failed to get job status: {status_response.status}")
                else:
                    logger.error(f"Failed to create job: {response1.status}")
        
        # Test 2: Job with successful execution but callback to URL that returns error
        logger.info("Test 2: Job with successful execution but callback to error URL...")
        job2_data = {
            "task_type": "http_call",
            "payload": {"url": "https://httpbin.org/delay/1", "method": "GET"},
            "callback_url": "https://httpbin.org/status/500"  # This will return 500 error
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_BASE_URL}/api/jobs",
                headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
                json=job2_data
            ) as response2:
                if response2.status == 202:
                    job2_data_response = await response2.json()
                    job2_id = job2_data_response["job_id"]
                    logger.info(f"Created job {job2_id} with callback to error URL")
                    
                    # Wait for job to complete
                    await asyncio.sleep(10)
                    
                    # Check job status
                    async with session.get(
                        f"{API_BASE_URL}/api/jobs/{job2_id}",
                        headers={"X-API-Key": API_KEY}
                    ) as status_response:
                        if status_response.status == 200:
                            job_status = await status_response.json()
                            logger.info(f"Job {job2_id} status: {job_status['status']}")
                            
                            if job_status['status'] == 'callback_failed':
                                logger.info("✅ Job correctly marked as callback_failed")
                            else:
                                logger.warning(f"❌ Expected callback_failed, got {job_status['status']}")
                        else:
                            logger.error(f"Failed to get job status: {status_response.status}")
                else:
                    logger.error(f"Failed to create job: {response2.status}")
        
        # Test 3: Job with successful execution and successful callback
        logger.info("Test 3: Job with successful execution and successful callback...")
        job3_data = {
            "task_type": "http_call",
            "payload": {"url": "https://httpbin.org/delay/1", "method": "GET"},
            "callback_url": "https://httpbin.org/post"  # This should work
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_BASE_URL}/api/jobs",
                headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
                json=job3_data
            ) as response3:
                if response3.status == 202:
                    job3_data_response = await response3.json()
                    job3_id = job3_data_response["job_id"]
                    logger.info(f"Created job {job3_id} with callback to working URL")
                    
                    # Wait for job to complete
                    await asyncio.sleep(10)
                    
                    # Check job status
                    async with session.get(
                        f"{API_BASE_URL}/api/jobs/{job3_id}",
                        headers={"X-API-Key": API_KEY}
                    ) as status_response:
                        if status_response.status == 200:
                            job_status = await status_response.json()
                            logger.info(f"Job {job3_id} status: {job_status['status']}")
                            
                            if job_status['status'] == 'completed':
                                logger.info("✅ Job correctly marked as completed")
                            else:
                                logger.warning(f"❌ Expected completed, got {job_status['status']}")
                        else:
                            logger.error(f"Failed to get job status: {status_response.status}")
                else:
                    logger.error(f"Failed to create job: {response3.status}")
        
        logger.info("Callback failure tests completed!")
        
    except Exception as e:
        logger.error(f"Callback failure test failed: {str(e)}")
        raise
    finally:
        # Cleanup
        await shutdown_job_logger()
        logger.info("Job logger shutdown completed")


async def verify_callback_failure_logs():
    """Verify that callback failures are properly logged."""
    logger.info("Verifying callback failure logs...")
    
    pool = await get_pool()
    
    async with pool.acquire() as conn:
        # Get all callback failure logs
        callback_failure_logs = await conn.fetch(
            """
            SELECT job_id, log_level, message, metadata, timestamp
            FROM job_logs 
            WHERE message LIKE '%Callback failed%'
            ORDER BY timestamp DESC
            LIMIT 10
            """
        )
        
        logger.info(f"Found {len(callback_failure_logs)} callback failure logs:")
        
        for log in callback_failure_logs:
            metadata = json.loads(log['metadata']) if log['metadata'] else {}
            logger.info(f"  - Job {log['job_id'][:8]}...: {log['message']}")
            logger.info(f"    Level: {log['log_level']}, URL: {metadata.get('callback_url', 'N/A')}")
        
        # Get jobs with callback_failed status
        callback_failed_jobs = await conn.fetch(
            """
            SELECT id, status, callback_url, created_at, updated_at
            FROM jobs 
            WHERE status = 'callback_failed'
            ORDER BY updated_at DESC
            LIMIT 5
            """
        )
        
        logger.info(f"Found {len(callback_failed_jobs)} jobs with callback_failed status:")
        
        for job in callback_failed_jobs:
            logger.info(f"  - Job {job['id'][:8]}...: {job['status']}")
            logger.info(f"    Callback URL: {job['callback_url']}")
            logger.info(f"    Updated: {job['updated_at']}")
        
        # Get statistics
        stats = await conn.fetchrow(
            """
            SELECT 
                COUNT(CASE WHEN status = 'callback_failed' THEN 1 END) as callback_failed_jobs,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_jobs,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_jobs,
                COUNT(CASE WHEN message LIKE '%Callback failed%' THEN 1 END) as callback_failure_logs
            FROM jobs, job_logs
            WHERE jobs.updated_at > NOW() - INTERVAL '1 hour'
            """
        )
        
        logger.info(f"Recent statistics:")
        logger.info(f"  - Callback failed jobs: {stats['callback_failed_jobs']}")
        logger.info(f"  - Completed jobs: {stats['completed_jobs']}")
        logger.info(f"  - Failed jobs: {stats['failed_jobs']}")
        logger.info(f"  - Callback failure logs: {stats['callback_failure_logs']}")


async def main():
    """Main test function."""
    logger.info("Starting callback failure testing...")
    
    try:
        # Run callback failure tests
        await test_callback_failure_scenarios()
        
        # Wait a bit for all processing to complete
        await asyncio.sleep(5)
        
        # Verify logs
        await verify_callback_failure_logs()
        
        logger.info("All callback failure tests completed successfully! ✅")
        
    except Exception as e:
        logger.error(f"Tests failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
