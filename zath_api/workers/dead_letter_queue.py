"""
Redis-based dead letter queue implementation.

This module provides functions to manage failed jobs in a Redis-based
dead letter queue system.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from config.redis import get_redis_client

logger = logging.getLogger(__name__)

# Redis key for dead letter queue
DEAD_LETTER_QUEUE_KEY = "dead_letter_queue"
DEAD_LETTER_QUEUE_METADATA_KEY = "dead_letter_queue_metadata"


async def add_to_dead_letter_queue(
    job_id: str, 
    task_type: str, 
    payload: Dict[str, Any], 
    error_message: str, 
    retry_count: int = 0, 
    max_retries: int = 3
) -> str:
    """
    Add a failed job to the Redis dead letter queue.
    
    Args:
        job_id: The UUID of the failed job
        task_type: Type of job that failed
        payload: Original job payload
        error_message: Error message from failure
        retry_count: Number of retry attempts made
        max_retries: Maximum retry attempts allowed
        
    Returns:
        The Redis key where the job was stored
    """
    try:
        redis_client = await get_redis_client()
        
        # Create dead letter job data
        dlq_job = {
            "job_id": job_id,
            "task_type": task_type,
            "payload": payload,
            "error_message": error_message,
            "retry_count": retry_count,
            "max_retries": max_retries,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Store in Redis list (FIFO order)
        job_data_json = json.dumps(dlq_job)
        await redis_client.lpush(DEAD_LETTER_QUEUE_KEY, job_data_json)
        
        # Update metadata for tracking
        metadata_key = f"{DEAD_LETTER_QUEUE_METADATA_KEY}:{job_id}"
        await redis_client.hset(metadata_key, mapping={
            "task_type": task_type,
            "retry_count": str(retry_count),
            "max_retries": str(max_retries),
            "created_at": dlq_job["created_at"],
            "updated_at": dlq_job["updated_at"]
        })
        
        # Set expiration for metadata (30 days)
        await redis_client.expire(metadata_key, 30 * 24 * 60 * 60)
        
        logger.info(f"Job {job_id} added to dead letter queue")
        return metadata_key
        
    except Exception as e:
        logger.error(f"Failed to add job {job_id} to dead letter queue: {str(e)}")
        raise


async def get_dead_letter_jobs(page: int = 1, limit: int = 20, task_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve a paginated list of dead letter queue jobs from Redis.
    
    Args:
        page: Page number (1-based)
        limit: Number of jobs per page
        task_type: Filter by task type (optional)
        
    Returns:
        Dictionary with dead letter jobs list and pagination info
    """
    try:
        redis_client = await get_redis_client()
        
        # Get all jobs from the dead letter queue
        all_jobs_data = await redis_client.lrange(DEAD_LETTER_QUEUE_KEY, 0, -1)
        
        # Parse and filter jobs
        jobs = []
        for job_data_json in all_jobs_data:
            try:
                job_data = json.loads(job_data_json)
                
                # Apply task type filter if specified
                if task_type and job_data.get("task_type") != task_type:
                    continue
                
                # Add a unique ID for the dead letter queue entry
                job_data["dlq_id"] = f"dlq_{hash(job_data_json) % 1000000}"
                jobs.append(job_data)
                
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to parse dead letter job data: {str(e)}")
                continue
        
        # Sort by creation time (newest first)
        jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        # Apply pagination
        total_count = len(jobs)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_jobs = jobs[start_idx:end_idx]
        
        return {
            "jobs": paginated_jobs,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count + limit - 1) // limit
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve dead letter jobs: {str(e)}")
        raise


async def retry_dead_letter_job(dlq_id: str) -> bool:
    """
    Retry a job from the dead letter queue by moving it back to the main queue.
    
    Args:
        dlq_id: The dead letter queue job ID
        
    Returns:
        True if job was successfully retried, False otherwise
    """
    try:
        redis_client = await get_redis_client()
        
        # Find the job in the dead letter queue
        all_jobs_data = await redis_client.lrange(DEAD_LETTER_QUEUE_KEY, 0, -1)
        
        job_to_retry = None
        job_index = None
        
        for i, job_data_json in enumerate(all_jobs_data):
            try:
                job_data = json.loads(job_data_json)
                current_dlq_id = f"dlq_{hash(job_data_json) % 1000000}"
                
                if current_dlq_id == dlq_id:
                    job_to_retry = job_data
                    job_index = i
                    break
                    
            except (json.JSONDecodeError, KeyError):
                continue
        
        if not job_to_retry:
            logger.warning(f"Dead letter job {dlq_id} not found")
            return False
        
        # Check if we've exceeded max retries
        if job_to_retry.get("retry_count", 0) >= job_to_retry.get("max_retries", 3):
            logger.warning(f"Job {job_to_retry['job_id']} has exceeded max retries")
            return False
        
        # Update retry count
        job_to_retry["retry_count"] = job_to_retry.get("retry_count", 0) + 1
        job_to_retry["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Move job back to main queue
        job_queue_data = {
            "job_id": job_to_retry["job_id"],
            "task_type": job_to_retry["task_type"],
            "payload": job_to_retry["payload"],
            "callback_url": None,  # Dead letter jobs don't have callbacks
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await redis_client.lpush("job_queue", json.dumps(job_queue_data))
        
        # Remove from dead letter queue
        await redis_client.lrem(DEAD_LETTER_QUEUE_KEY, 1, json.dumps(job_to_retry))
        
        # Update metadata
        metadata_key = f"{DEAD_LETTER_QUEUE_METADATA_KEY}:{job_to_retry['job_id']}"
        await redis_client.hset(metadata_key, mapping={
            "task_type": job_to_retry["task_type"],
            "retry_count": str(job_to_retry["retry_count"]),
            "max_retries": str(job_to_retry["max_retries"]),
            "created_at": job_to_retry["created_at"],
            "updated_at": job_to_retry["updated_at"]
        })
        
        logger.info(f"Job {job_to_retry['job_id']} retried from dead letter queue")
        return True
        
    except Exception as e:
        logger.error(f"Failed to retry dead letter job {dlq_id}: {str(e)}")
        return False


async def remove_dead_letter_job(dlq_id: str) -> bool:
    """
    Remove a job from the dead letter queue permanently.
    
    Args:
        dlq_id: The dead letter queue job ID
        
    Returns:
        True if job was successfully removed, False otherwise
    """
    try:
        redis_client = await get_redis_client()
        
        # Find and remove the job from the dead letter queue
        all_jobs_data = await redis_client.lrange(DEAD_LETTER_QUEUE_KEY, 0, -1)
        
        for job_data_json in all_jobs_data:
            try:
                job_data = json.loads(job_data_json)
                current_dlq_id = f"dlq_{hash(job_data_json) % 1000000}"
                
                if current_dlq_id == dlq_id:
                    # Remove from dead letter queue
                    await redis_client.lrem(DEAD_LETTER_QUEUE_KEY, 1, job_data_json)
                    
                    # Remove metadata
                    metadata_key = f"{DEAD_LETTER_QUEUE_METADATA_KEY}:{job_data['job_id']}"
                    await redis_client.delete(metadata_key)
                    
                    logger.info(f"Job {job_data['job_id']} removed from dead letter queue")
                    return True
                    
            except (json.JSONDecodeError, KeyError):
                continue
        
        logger.warning(f"Dead letter job {dlq_id} not found for removal")
        return False
        
    except Exception as e:
        logger.error(f"Failed to remove dead letter job {dlq_id}: {str(e)}")
        return False


async def get_dead_letter_queue_stats() -> Dict[str, Any]:
    """
    Get statistics about the dead letter queue.
    
    Returns:
        Dictionary with dead letter queue statistics
    """
    try:
        redis_client = await get_redis_client()
        
        # Get total count
        total_count = await redis_client.llen(DEAD_LETTER_QUEUE_KEY)
        
        # Get task type breakdown
        all_jobs_data = await redis_client.lrange(DEAD_LETTER_QUEUE_KEY, 0, -1)
        task_type_counts = {}
        
        for job_data_json in all_jobs_data:
            try:
                job_data = json.loads(job_data_json)
                task_type = job_data.get("task_type", "unknown")
                task_type_counts[task_type] = task_type_counts.get(task_type, 0) + 1
            except (json.JSONDecodeError, KeyError):
                continue
        
        return {
            "total_jobs": total_count,
            "task_type_breakdown": task_type_counts,
            "queue_name": DEAD_LETTER_QUEUE_KEY
        }
        
    except Exception as e:
        logger.error(f"Failed to get dead letter queue stats: {str(e)}")
        return {
            "total_jobs": 0,
            "task_type_breakdown": {},
            "queue_name": DEAD_LETTER_QUEUE_KEY,
            "error": str(e)
        }
