"""
Job worker for processing jobs from Redis queue

This module provides a robust job processing system that:
- Listens to Redis queue for new jobs
- Processes jobs with configurable delays
- Updates job status in database
- Sends webhook callbacks
- Handles errors gracefully
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Dict, Any, Optional

import aiohttp
from dotenv import load_dotenv

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.redis import get_redis_client, test_redis_connection
from db.connection import get_pool, init_db_pool
from workers.task_handlers import execute_task
from workers.dead_letter_queue import add_to_dead_letter_queue

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class JobWorker:
    """
    Asynchronous job worker that processes jobs from Redis queue.
    
    Features:
    - Continuous job polling from Redis
    - Database status updates
    - Webhook callback support
    - Graceful error handling
    - Configurable processing delays
    """
    
    def __init__(self, processing_delay: int = 2):
        """
        Initialize the job worker.
        
        Args:
            processing_delay: Delay in seconds to simulate job processing
        """
        self.running = False
        self.db_pool = None
        self.processing_delay = processing_delay
        self.session = None
        
        # Debug: Log Redis configuration
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = os.getenv("REDIS_PORT", "6379")
        logger.info(f"Redis configuration: {redis_host}:{redis_port}")
    
    async def _initialize_connections(self) -> bool:
        """
        Initialize database and HTTP session connections.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Test Redis connection
            if not await test_redis_connection():
                logger.error("Redis connection failed")
                return False
            logger.info("Redis connection established")
            
            # Initialize database connection
            await init_db_pool()
            self.db_pool = await get_pool()
            logger.info("Database connection established")
            
            # Initialize HTTP session for callbacks
            self.session = aiohttp.ClientSession()
            logger.info("HTTP session initialized")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize connections: {str(e)}")
            return False
    
    async def _cleanup_connections(self):
        """Clean up database and HTTP connections."""
        try:
            if self.session:
                await self.session.close()
                logger.info("HTTP session closed")
        except Exception as e:
            logger.error(f"Error closing HTTP session: {str(e)}")
    
    async def process_job(self, job_data: Dict[str, Any]) -> bool:
        """
        Process a single job from the queue using task-specific handlers.
        
        Args:
            job_data: Job data containing id, task_type, payload, and callback_url
            
        Returns:
            True if job processed successfully, False otherwise
        """
        job_id = job_data["job_id"]
        task_type = job_data["task_type"]
        payload = job_data["payload"]
        callback_url = job_data.get("callback_url")
        
        logger.info(f"Processing job {job_id} of type {task_type}")
        
        try:
            # Update job status to in_progress
            await self._update_job_status(job_id, "in_progress")
            
            # Execute the task using the appropriate handler
            success, result, error_message = await execute_task(task_type, payload)
            
            if success:
                # Update job status to completed
                await self._update_job_status(job_id, "completed")
                
                # Send callback if URL provided
                if callback_url:
                    callback_success = await self._send_callback(callback_url, job_id, "completed", result=result)
                    if not callback_success:
                        logger.warning(f"Job {job_id} completed but callback failed after all retries")
                    else:
                        logger.info(f"Job {job_id} completed and callback sent successfully")
                
                logger.info(f"Job {job_id} completed successfully")
                return True
            else:
                # Task execution failed - send to dead letter queue
                logger.error(f"Job {job_id} failed: {error_message}")
                
                try:
                    # Add to dead letter queue
                    await add_to_dead_letter_queue(
                        job_id=job_id,
                        task_type=task_type,
                        payload=payload,
                        error_message=error_message,
                        retry_count=0,
                        max_retries=3
                    )
                    
                    # Update job status to failed
                    await self._update_job_status(job_id, "failed")
                    
                    # Send failure callback if URL provided
                    if callback_url:
                        callback_success = await self._send_callback(callback_url, job_id, "failed", error=error_message)
                        if not callback_success:
                            logger.warning(f"Job {job_id} failed and callback also failed after all retries")
                        else:
                            logger.info(f"Job {job_id} failed but callback sent successfully")
                    
                    logger.info(f"Job {job_id} moved to dead letter queue")
                    return False
                    
                except Exception as dlq_error:
                    logger.error(f"Failed to add job {job_id} to dead letter queue: {str(dlq_error)}")
                    # Still update job status to failed
                    await self._update_job_status(job_id, "failed")
                    return False
            
        except Exception as e:
            logger.error(f"Job {job_id} failed with unexpected error: {str(e)}")
            
            try:
                # Add to dead letter queue for unexpected errors
                await add_to_dead_letter_queue(
                    job_id=job_id,
                    task_type=task_type,
                    payload=payload,
                    error_message=f"Unexpected error: {str(e)}",
                    retry_count=0,
                    max_retries=3
                )
                
                # Update job status to failed
                await self._update_job_status(job_id, "failed")
                
                # Send failure callback if URL provided
                if callback_url:
                    callback_success = await self._send_callback(callback_url, job_id, "failed", error=str(e))
                    if not callback_success:
                        logger.warning(f"Job {job_id} failed and callback also failed after all retries")
                    else:
                        logger.info(f"Job {job_id} failed but callback sent successfully")
                
                logger.info(f"Job {job_id} moved to dead letter queue due to unexpected error")
                return False
                
            except Exception as update_error:
                logger.error(f"Failed to update job {job_id} status: {str(update_error)}")
                return False
    
    async def _update_job_status(self, job_id: str, status: str):
        """
        Update job status in the database.
        
        Args:
            job_id: Unique job identifier
            status: New status (completed, failed, etc.)
        """
        try:
            if not self.db_pool:
                logger.warning("Database pool not available, attempting to reconnect")
                await init_db_pool()
                self.db_pool = await get_pool()
            
            logger.info(f"Updating job {job_id} status to {status}")
            
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    "UPDATE jobs SET status = $1, updated_at = NOW() WHERE id = $2",
                    status, job_id
                )
            
            logger.info(f"Successfully updated job {job_id} status to {status}")
            
        except Exception as e:
            logger.error(f"Failed to update job {job_id} status: {str(e)}")
            raise
    
    async def _update_callback_retry_count(self, job_id: str, retry_count: int):
        """
        Update callback retry count in the database.
        
        Args:
            job_id: Unique job identifier
            retry_count: Number of retry attempts made
        """
        try:
            if not self.db_pool:
                logger.warning("Database pool not available, attempting to reconnect")
                await init_db_pool()
                self.db_pool = await get_pool()
            
            logger.info(f"Updating callback retry count for job {job_id} to {retry_count}")
            
            async with self.db_pool.acquire() as conn:
                result = await conn.execute(
                    "UPDATE jobs SET callback_retry_count = $1, updated_at = NOW() WHERE id = $2",
                    retry_count, job_id
                )
                
                # Check if the update actually affected a row
                if result == "UPDATE 0":
                    logger.warning(f"No job found with ID {job_id} for callback retry count update")
                else:
                    logger.info(f"Successfully updated callback retry count for job {job_id} to {retry_count}")
            
        except Exception as e:
            logger.error(f"Failed to update callback retry count for job {job_id}: {str(e)}")
            # Don't raise here as this is not critical for job processing
    
    async def _send_callback(self, callback_url: str, job_id: str, status: str, error: str = None, result: Dict[str, Any] = None):
        """
        Send callback to webhook URL with retry logic.
        
        Args:
            callback_url: Webhook URL to send callback to
            job_id: Job identifier
            status: Job status
            error: Error message (if any)
            result: Task execution result (if successful)
        """
        max_retries = 3
        retry_delays = [1, 5, 15]  # Exponential backoff: 1s, 5s, 15s
        
        callback_data = {
            "job_id": job_id,
            "status": status,
            "completed_at": datetime.now(timezone.utc).isoformat()
        }
        
        if error:
            callback_data["error"] = error
        
        if result:
            callback_data["result"] = result
        
        for attempt in range(max_retries + 1):  # 0, 1, 2, 3 (4 attempts total)
            try:
                if not self.session:
                    logger.warning("HTTP session not available, creating new session")
                    self.session = aiohttp.ClientSession()
                
                logger.info(f"Attempting callback to {callback_url} (attempt {attempt + 1}/{max_retries + 1})")
                
                async with self.session.post(callback_url, json=callback_data) as response:
                    if response.status >= 200 and response.status < 300:
                        logger.info(f"Callback sent successfully to {callback_url}, status: {response.status}")
                        # Update retry count to 0 on success
                        await self._update_callback_retry_count(job_id, 0)
                        return True
                    else:
                        error_msg = f"HTTP {response.status} response from {callback_url}"
                        logger.warning(f"Callback attempt {attempt + 1} failed: {error_msg}")
                        
                        if attempt < max_retries:
                            delay = retry_delays[attempt]
                            logger.info(f"Retrying callback in {delay} seconds...")
                            await asyncio.sleep(delay)
                        else:
                            logger.error(f"All callback attempts failed for job {job_id}. Final error: {error_msg}")
                            await self._update_callback_retry_count(job_id, max_retries + 1)
                            return False
                            
            except Exception as e:
                error_msg = f"Connection error: {str(e)}"
                logger.warning(f"Callback attempt {attempt + 1} failed: {error_msg}")
                
                if attempt < max_retries:
                    delay = retry_delays[attempt]
                    logger.info(f"Retrying callback in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All callback attempts failed for job {job_id}. Final error: {error_msg}")
                    await self._update_callback_retry_count(job_id, max_retries + 1)
                    return False
        
        return False
    
    async def _process_queue(self):
        """Main queue processing loop."""
        while self.running:
            try:
                # Wait for job from Redis queue with timeout
                redis_client = await get_redis_client()
                result = await redis_client.brpop("job_queue", timeout=1)
                
                if result:
                    _, job_data_json = result
                    job_data = json.loads(job_data_json)
                    await self.process_job(job_data)
                else:
                    # No jobs in queue, continue polling
                    continue
                    
            except asyncio.CancelledError:
                logger.info("Queue processing cancelled")
                break
            except Exception as e:
                logger.error(f"Error in queue processing: {str(e)}")
                await asyncio.sleep(1)  # Brief pause before retrying
    
    async def start(self):
        """Start the job worker."""
        logger.info("Starting job worker...")
        
        # Initialize connections
        if not await self._initialize_connections():
            logger.error("Failed to initialize connections, worker cannot start")
            return
        
        self.running = True
        logger.info("Job worker started successfully")
        
        try:
            await self._process_queue()
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the job worker gracefully."""
        logger.info("Stopping job worker...")
        self.running = False
        
        # Cleanup connections
        await self._cleanup_connections()
        logger.info("Job worker stopped")


async def main():
    """Main entry point for the worker."""
    worker = JobWorker()
    
    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Worker interrupted by user")
    except Exception as e:
        logger.error(f"Worker failed with error: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
