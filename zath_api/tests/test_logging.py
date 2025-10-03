#!/usr/bin/env python3
"""
Test script for the logging and monitoring module.

This script tests:
1. Job logger initialization
2. Log entry creation and batching
3. Database insertion
4. Log retrieval and verification
"""

import asyncio
import json
import logging
import sys
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.connection import init_db_pool, get_pool
from utils.job_logger import (
    get_job_logger, log_job_started, log_job_completed, log_job_failed,
    log_job_retry, log_job_cancelled, log_worker_event, shutdown_job_logger,
    LogLevel
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_job_logger():
    """Test the job logger functionality."""
    logger.info("Starting job logger tests...")
    
    try:
        # Initialize database connection
        await init_db_pool()
        logger.info("Database connection initialized")
        
        # Get job logger instance
        job_logger = await get_job_logger()
        logger.info("Job logger instance created")
        
        # Test job ID (using valid UUIDs)
        test_job_id = str(uuid.uuid4())
        
        # Test 1: Log job started
        logger.info("Test 1: Logging job start...")
        await log_job_started(test_job_id, "http_call", {"url": "https://example.com", "method": "GET"})
        
        # Test 2: Log worker events
        logger.info("Test 2: Logging worker events...")
        await log_worker_event(test_job_id, "task_execution_started", {"handler": "http_call_handler"})
        await log_worker_event(test_job_id, "http_request_sent", {"url": "https://example.com", "status_code": 200})
        
        # Test 3: Log job completion
        logger.info("Test 3: Logging job completion...")
        result = {"status_code": 200, "response_time": 1.5, "data_size": 1024}
        await log_job_completed(test_job_id, result, duration=2.5)
        
        # Test 4: Log job failure scenario
        logger.info("Test 4: Logging job failure...")
        failed_job_id = str(uuid.uuid4())
        await log_job_started(failed_job_id, "data_transform", {"input": "test_data"})
        await log_job_failed(failed_job_id, "Invalid input format", retry_count=1, max_retries=3)
        
        # Test 5: Log job retry
        logger.info("Test 5: Logging job retry...")
        await log_job_retry(failed_job_id, 2, "Previous attempt failed due to network timeout")
        
        # Test 6: Log job cancellation
        logger.info("Test 6: Logging job cancellation...")
        cancelled_job_id = str(uuid.uuid4())
        await log_job_started(cancelled_job_id, "email_send", {"to": "test@example.com"})
        await log_job_cancelled(cancelled_job_id, "User requested cancellation")
        
        # Test 7: Batch logging with multiple entries
        logger.info("Test 7: Testing batch logging...")
        batch_job_id = str(uuid.uuid4())
        await log_job_started(batch_job_id, "report_generate", {"report_type": "monthly"})
        
        # Add multiple log entries quickly to test batching
        for i in range(10):
            await log_worker_event(batch_job_id, f"processing_step_{i}", {"step": i, "progress": f"{i*10}%"})
        
        await log_job_completed(batch_job_id, {"report_size": 5000, "pages": 25}, duration=15.2)
        
        # Force flush to ensure all logs are written
        logger.info("Flushing logs to database...")
        await job_logger.flush()
        
        # Test 8: Verify logs in database
        logger.info("Test 8: Verifying logs in database...")
        await verify_logs_in_database([test_job_id, failed_job_id, cancelled_job_id, batch_job_id])
        
        logger.info("All job logger tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Job logger test failed: {str(e)}")
        raise
    finally:
        # Cleanup
        await shutdown_job_logger()
        logger.info("Job logger shutdown completed")


async def verify_logs_in_database(job_ids: list):
    """Verify that logs were properly inserted into the database."""
    pool = await get_pool()
    
    async with pool.acquire() as conn:
        for job_id in job_ids:
            # Get all logs for this job
            logs = await conn.fetch(
                """
                SELECT id, job_id, log_level, message, timestamp, metadata
                FROM job_logs 
                WHERE job_id = $1 
                ORDER BY timestamp ASC
                """,
                job_id
            )
            
            logger.info(f"Found {len(logs)} log entries for job {job_id}")
            
            for log in logs:
                metadata = json.loads(log['metadata']) if log['metadata'] else {}
                logger.info(f"  - {log['log_level']}: {log['message']} (metadata: {metadata})")
            
            # Verify we have at least some logs
            assert len(logs) > 0, f"No logs found for job {job_id}"
            
            # Verify log levels are valid
            valid_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
            for log in logs:
                assert log['log_level'] in valid_levels, f"Invalid log level: {log['log_level']}"
            
            # Verify timestamps are recent (within last hour)
            now = datetime.now(timezone.utc)
            for log in logs:
                time_diff = (now - log['timestamp']).total_seconds()
                assert time_diff < 3600, f"Log timestamp too old: {log['timestamp']}"
        
        # Get overall statistics
        stats = await conn.fetchrow(
            """
            SELECT 
                COUNT(*) as total_logs,
                COUNT(DISTINCT job_id) as unique_jobs,
                COUNT(CASE WHEN log_level = 'INFO' THEN 1 END) as info_logs,
                COUNT(CASE WHEN log_level = 'ERROR' THEN 1 END) as error_logs,
                COUNT(CASE WHEN log_level = 'WARNING' THEN 1 END) as warning_logs
            FROM job_logs 
            WHERE timestamp > NOW() - INTERVAL '1 hour'
            """
        )
        
        logger.info(f"Database verification complete:")
        logger.info(f"  - Total logs: {stats['total_logs']}")
        logger.info(f"  - Unique jobs: {stats['unique_jobs']}")
        logger.info(f"  - INFO logs: {stats['info_logs']}")
        logger.info(f"  - ERROR logs: {stats['error_logs']}")
        logger.info(f"  - WARNING logs: {stats['warning_logs']}")


async def test_performance():
    """Test logging performance with many entries."""
    logger.info("Testing logging performance...")
    
    job_logger = await get_job_logger()
    start_time = datetime.now(timezone.utc)
    
    # Create many log entries
    num_entries = 100
    for i in range(num_entries):
        job_id = str(uuid.uuid4())
        await log_job_started(job_id, "http_call", {"test": True})
        await log_worker_event(job_id, "performance_test", {"iteration": i})
        await log_job_completed(job_id, {"result": f"test_{i}"}, duration=0.1)
    
    # Force flush
    await job_logger.flush()
    
    end_time = datetime.now(timezone.utc)
    duration = (end_time - start_time).total_seconds()
    
    logger.info(f"Performance test completed:")
    logger.info(f"  - {num_entries} jobs logged in {duration:.2f} seconds")
    logger.info(f"  - Average: {num_entries/duration:.1f} jobs/second")
    logger.info(f"  - Average: {duration/num_entries*1000:.1f} ms per job")


async def main():
    """Main test function."""
    logger.info("Starting logging and monitoring module tests...")
    
    try:
        # Run basic functionality tests
        await test_job_logger()
        
        # Run performance tests
        await test_performance()
        
        logger.info("All tests completed successfully! ✅")
        
    except Exception as e:
        logger.error(f"Tests failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
