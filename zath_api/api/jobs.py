"""
Jobs API - Self-sufficient implementation

Contains models, validation, database operations, and endpoints for job management
and Redis-based dead letter queue functionality.
"""
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional

import asyncpg
from fastapi import APIRouter, HTTPException, Request, Query, status
from pydantic import BaseModel, Field, HttpUrl, validator

from config.redis import get_redis_client
from db.connection import get_pool
from workers.dead_letter_queue import (
    get_dead_letter_jobs,
    get_dead_letter_queue_stats,
    retry_dead_letter_job
)

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Jobs"])

# Utility Functions
def validate_uuid(uuid_string: str) -> bool:
    """
    Validate if a string is a valid UUID format.
    
    Args:
        uuid_string: String to validate
        
    Returns:
        True if valid UUID, False otherwise
    """
    try:
        uuid.UUID(uuid_string)
        return True
    except ValueError:
        return False

# Data Models
class JobCreate(BaseModel):
    """
    Request model for creating a new job.
    
    Attributes:
        task_type: Type of job to execute (e.g., 'email_send', 'data_process')
        payload: JSON data required for job execution
        callback_url: Optional webhook URL for job completion notifications
    """
    task_type: str = Field(..., description="Type of job to execute (e.g., 'email_send', 'data_process')")
    payload: Dict[str, Any] = Field(..., description="JSON data required for job execution")
    callback_url: Optional[HttpUrl] = Field(None, description="Optional webhook URL for job completion notifications")
    
    @validator('task_type')
    def validate_task_type(cls, v):
        if not v or not v.strip():
            raise ValueError('task_type cannot be empty')
        
        valid_task_types = {
            'http_call', 'data_transform', 'email_send', 
            'webhook_call', 'file_upload', 'report_generate'
        }
        
        task_type = v.strip()
        if task_type not in valid_task_types:
            raise ValueError(f'Invalid task_type: {task_type}. Must be one of: {", ".join(sorted(valid_task_types))}')
        
        return task_type

class JobResponse(BaseModel):
    """
    Response model for job creation.
    
    Attributes:
        job_id: Unique identifier for the job (UUID)
        status: Current job status (always "queued" initially)
        created_at: ISO timestamp when job was created
    """
    job_id: str = Field(..., description="Unique identifier for the job (UUID)")
    status: str = Field(..., description="Current job status (always 'queued' initially)")
    created_at: str = Field(..., description="ISO timestamp when job was created")

class JobStatusResponse(BaseModel):
    """
    Response model for job status retrieval.
    
    Attributes:
        job_id: Unique identifier for the job (UUID)
        task_type: Type of job being executed
        status: Current job status (queued, in_progress, completed, failed)
        payload: Job payload data (if accessible)
        callback_url: Webhook URL for notifications (if provided)
        created_at: ISO timestamp when job was created
        updated_at: ISO timestamp when job was last updated
        retry_count: Number of job retry attempts made
        callback_retry_count: Number of callback retry attempts made
    """
    job_id: str = Field(..., description="Unique identifier for the job (UUID)")
    task_type: str = Field(..., description="Type of job being executed")
    status: str = Field(..., description="Current job status (queued, in_progress, completed, failed)")
    payload: Optional[Dict[str, Any]] = Field(None, description="Job payload data")
    callback_url: Optional[str] = Field(None, description="Webhook URL for notifications")
    created_at: str = Field(..., description="ISO timestamp when job was created")
    updated_at: Optional[str] = Field(None, description="ISO timestamp when job was last updated")
    retry_count: int = Field(..., description="Number of job retry attempts made")
    callback_retry_count: int = Field(..., description="Number of callback retry attempts made")

class JobListItem(BaseModel):
    """
    Response model for job list items.
    
    Attributes:
        job_id: Unique identifier for the job (UUID)
        task_type: Type of job being executed
        status: Current job status
        callback_url: Webhook URL for notifications (if provided)
        retry_count: Number of job retry attempts made
        callback_retry_count: Number of callback retry attempts made
        created_at: ISO timestamp when job was created
        updated_at: ISO timestamp when job was last updated
    """
    job_id: str = Field(..., description="Unique identifier for the job (UUID)")
    task_type: str = Field(..., description="Type of job being executed")
    status: str = Field(..., description="Current job status")
    callback_url: Optional[str] = Field(None, description="Webhook URL for notifications")
    retry_count: int = Field(..., description="Number of job retry attempts made")
    callback_retry_count: int = Field(..., description="Number of callback retry attempts made")
    created_at: str = Field(..., description="ISO timestamp when job was created")
    updated_at: Optional[str] = Field(None, description="ISO timestamp when job was last updated")

class JobListResponse(BaseModel):
    """
    Response model for job list with pagination.
    
    Attributes:
        jobs: List of job items
        pagination: Pagination information
    """
    jobs: list[JobListItem] = Field(..., description="List of jobs")
    pagination: Dict[str, Any] = Field(..., description="Pagination information")

class DeadLetterJob(BaseModel):
    """
    Model for dead letter queue jobs.
    
    Attributes:
        dlq_id: Dead letter queue job ID
        job_id: Original job ID
        task_type: Type of job that failed
        payload: Original job payload
        error_message: Error message from failure
        retry_count: Number of retry attempts made
        max_retries: Maximum retry attempts allowed
        created_at: When the job was moved to dead letter queue
        updated_at: When the entry was last updated
    """
    dlq_id: str = Field(..., description="Dead letter queue job ID")
    job_id: str = Field(..., description="Original job ID")
    task_type: str = Field(..., description="Type of job that failed")
    payload: Optional[Dict[str, Any]] = Field(None, description="Original job payload")
    error_message: str = Field(..., description="Error message from failure")
    retry_count: int = Field(..., description="Number of retry attempts made")
    max_retries: int = Field(..., description="Maximum retry attempts allowed")
    created_at: str = Field(..., description="When the job was moved to dead letter queue")
    updated_at: Optional[str] = Field(None, description="When the entry was last updated")

class DeadLetterListResponse(BaseModel):
    """
    Response model for dead letter queue list with pagination.
    
    Attributes:
        jobs: List of dead letter jobs
        pagination: Pagination information
    """
    jobs: list[DeadLetterJob] = Field(..., description="List of dead letter jobs")
    pagination: Dict[str, Any] = Field(..., description="Pagination information")

# Database Operations (self-contained)
async def create_job_in_db(task_type: str, payload: dict, callback_url: str = None, user_email: str = None) -> str:
    """Create a new job in the database and return job_id"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        job_id = await conn.fetchval(
            """
            INSERT INTO jobs (id, user_email, task_type, payload, callback_url, status)
            VALUES (gen_random_uuid(), $1, $2, $3, $4, 'queued')
            RETURNING id
            """,
            user_email, task_type, json.dumps(payload), str(callback_url) if callback_url else None
        )
        return str(job_id)

async def get_job_by_id(job_id: str, user_email: str = None) -> Optional[Dict[str, Any]]:
    """
    Retrieve a job by its ID from the database.
    
    Args:
        job_id: The UUID of the job to retrieve
        user_email: Email of the authenticated user (for job isolation)
        
    Returns:
        Job data as dictionary or None if not found
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Build WHERE clause for security
        where_conditions = ["id = $1"]
        params = [job_id]
        
        if user_email:
            where_conditions.append("user_email = $2")
            params.append(user_email)
        
        where_clause = " AND ".join(where_conditions)
        
        job = await conn.fetchrow(
            f"""
            SELECT id, task_type, payload, callback_url, status, 
                   retry_count, callback_retry_count, created_at, updated_at
            FROM jobs 
            WHERE {where_clause}
            """,
            *params
        )
        
        if job:
            # Handle payload - it might be stored as JSONB (dict) or as string
            payload = job['payload']
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except (json.JSONDecodeError, TypeError):
                    payload = None
            
            return {
                "job_id": str(job['id']),  # Changed from 'id' to 'job_id'
                "task_type": job['task_type'],
                "payload": payload,
                "callback_url": job['callback_url'],
                "status": job['status'],
                "retry_count": job['retry_count'],
                "callback_retry_count": job['callback_retry_count'],
                "created_at": job['created_at'].isoformat() if job['created_at'] else None,
                "updated_at": job['updated_at'].isoformat() if job['updated_at'] else None
            }
        return None

async def get_jobs_list(page: int = 1, limit: int = 20, status: str = None, task_type: str = None, user_email: str = None) -> Dict[str, Any]:
    """
    Retrieve a paginated list of jobs with optional filtering.
    
    Args:
        page: Page number (1-based)
        limit: Number of jobs per page
        status: Filter by job status
        task_type: Filter by task type
        user_email: Email of the authenticated user (for job isolation)
        
    Returns:
        Dictionary with jobs list and pagination info
    """
    pool = await get_pool()
    offset = (page - 1) * limit
    
    # Build WHERE clause for filters
    where_conditions = []
    params = []
    param_count = 0
    
    # Always filter by user email for security
    if user_email:
        param_count += 1
        where_conditions.append(f"user_email = ${param_count}")
        params.append(user_email)
    
    if status:
        param_count += 1
        where_conditions.append(f"status = ${param_count}")
        params.append(status)
    
    if task_type:
        param_count += 1
        where_conditions.append(f"task_type = ${param_count}")
        params.append(task_type)
    
    where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
    
    # Get total count
    count_query = f"SELECT COUNT(*) FROM jobs{where_clause}"
    total_count = await pool.fetchval(count_query, *params)
    
    # Get jobs with pagination
    param_count += 1
    jobs_query = f"""
        SELECT id, task_type, status, callback_url, retry_count, callback_retry_count, 
               created_at, updated_at
        FROM jobs{where_clause}
        ORDER BY created_at DESC
        LIMIT ${param_count} OFFSET ${param_count + 1}
    """
    params.extend([limit, offset])
    
    jobs = await pool.fetch(jobs_query, *params)
    
    # Process jobs
    jobs_list = []
    for job in jobs:
        jobs_list.append({
            "job_id": str(job['id']),
            "task_type": job['task_type'],
            "status": job['status'],
            "callback_url": job['callback_url'],
            "retry_count": job['retry_count'],
            "callback_retry_count": job['callback_retry_count'],
            "created_at": job['created_at'].isoformat() if job['created_at'] else None,
            "updated_at": job['updated_at'].isoformat() if job['updated_at'] else None,
        })
    
    return {
        "jobs": jobs_list,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total_count,
            "pages": (total_count + limit - 1) // limit
        }
    }

# Note: Dead letter queue operations are now handled by workers/dead_letter_queue.py
# This uses Redis instead of database tables for better performance

# API Endpoint
@router.post("/jobs", response_model=JobResponse, status_code=202)
async def create_job(job_data: JobCreate, request: Request):
    """
    Create a new asynchronous job in the ZATH system.
    
    This endpoint accepts a job specification and creates a new job record in the database.
    The job will be queued for processing by the job workers.
    
    ## Request Body
    
    - **task_type** (string, required): Type of job to execute. Examples:
      - `email_send` - Send an email
      - `data_process` - Process data files
      - `webhook_call` - Make HTTP webhook calls
      - `file_upload` - Upload files to storage
      - `report_generate` - Generate reports
    
    - **payload** (object, required): JSON data required for job execution.
      The structure depends on the task_type. Examples:
      
      For `email_send`:
      ```json
      {
        "to": "user@example.com",
        "subject": "Hello World",
        "body": "This is the email content"
      }
      ```
      
      For `data_process`:
      ```json
      {
        "file_id": "12345",
        "format": "csv",
        "options": {
          "delimiter": ",",
          "encoding": "utf-8"
        }
      }
      ```
    
    - **callback_url** (string, optional): Webhook URL for job completion notifications.
      When the job completes, a POST request will be sent to this URL with job status.
      Must be a valid HTTP/HTTPS URL.
    
    ## Response
    
    Returns a 202 Accepted status with job details:
    
    - **job_id** (string): Unique identifier for the job (UUID)
    - **status** (string): Current job status (always "queued" initially)
    - **created_at** (string): ISO timestamp when job was created
    
    ## Authentication
    
    Requires valid API key in header:
    - `X-API-Key: your_api_key_here`
    - `Authorization: Bearer your_api_key_here`
    
    ## Example Usage
    
    ```bash
    curl -X POST "http://localhost:8000/api/jobs" \\
         -H "Content-Type: application/json" \\
         -H "X-API-Key: your_api_key" \\
         -d '{
           "task_type": "email_send",
           "payload": {
             "to": "user@example.com",
             "subject": "Hello World",
             "body": "This is a test email"
           },
           "callback_url": "https://webhook.site/abc123"
         }'
    ```
    
    ## Error Responses
    
    - **400 Bad Request**: Invalid input data
    - **401 Unauthorized**: Missing or invalid API key
    - **422 Unprocessable Content**: Validation errors (empty task_type, invalid URL, etc.)
    - **500 Internal Server Error**: Database or server errors
    
    ## Job Lifecycle
    
    1. **Created**: Job is created with status "queued"
    2. **Processing**: Job workers pick up the job
    3. **Completed**: Job finishes successfully
    4. **Failed**: Job encounters an error
    
    ## Notes
    
    - Jobs are processed asynchronously by background workers
    - Job status updates are sent to callback_url if provided
    - Job payload is stored as JSONB in the database
    - All jobs start with status "queued"
    """
    try:
        # User is already authenticated via middleware
        user = request.state.user
        
        # Create job in database
        job_id = await create_job_in_db(
            job_data.task_type,
            job_data.payload,
            job_data.callback_url,
            user['email']
        )
        
        # Push job to Redis queue
        try:
            job_queue_data = {
                "job_id": job_id,
                "task_type": job_data.task_type,
                "payload": job_data.payload,
                "callback_url": str(job_data.callback_url) if job_data.callback_url else None,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            redis_client = await get_redis_client()
            await redis_client.lpush("job_queue", json.dumps(job_queue_data))
        except Exception as redis_error:
            # Log Redis error but don't fail the job creation
            # The job is already in the database and can be processed later
            logger.warning(f"Failed to push job to Redis queue: {redis_error}")
            # In production, you might want to log this to a proper logging system
        
        return JobResponse(
            job_id=job_id,
            status="queued",
            created_at=datetime.now(timezone.utc).isoformat()
        )
        
    except asyncpg.UniqueViolationError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Job with this ID already exists"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job: {str(e)}"
        )

@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str, request: Request):
    """
    Retrieve the status and details of a specific job.
    
    This endpoint returns the current status and all relevant information
    about a job identified by its job_id.
    
    ## Path Parameters
    
    - **job_id** (string, required): The UUID of the job to retrieve
    
    ## Response
    
    Returns job details including:
    
    - **job_id** (string): Unique identifier for the job (UUID)
    - **task_type** (string): Type of job being executed
    - **status** (string): Current job status:
      - `queued` - Job is waiting to be processed
      - `in_progress` - Job is currently being processed
      - `completed` - Job has finished successfully
      - `failed` - Job encountered an error
    - **payload** (object, optional): Job payload data
    - **callback_url** (string, optional): Webhook URL for notifications
    - **created_at** (string): ISO timestamp when job was created
    - **updated_at** (string, optional): ISO timestamp when job was last updated
    - **retry_count** (integer): Number of job retry attempts made
    - **callback_retry_count** (integer): Number of callback retry attempts made
    
    ## Authentication
    
    Requires valid API key in header:
    - `X-API-Key: your_api_key_here`
    - `Authorization: Bearer your_api_key_here`
    
    ## Example Usage
    
    ```bash
    curl -X GET "http://localhost:8000/api/jobs/123e4567-e89b-12d3-a456-426614174000" \\
         -H "X-API-Key: your_api_key"
    ```
    
    ## Example Response
    
    ```json
    {
      "job_id": "123e4567-e89b-12d3-a456-426614174000",
      "task_type": "email_send",
      "status": "completed",
      "payload": {
        "to": "user@example.com",
        "subject": "Hello World",
        "body": "This is a test email"
      },
      "callback_url": "https://webhook.site/abc123",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:05Z",
      "retry_count": 0,
      "callback_retry_count": 0
    }
    ```
    
    ## Error Responses
    
    - **401 Unauthorized**: Missing or invalid API key
    - **404 Not Found**: Job with the specified ID does not exist
    - **422 Unprocessable Content**: Invalid job_id format (not a valid UUID)
    - **500 Internal Server Error**: Database or server errors
    
    ## Status Values
    
    - **queued**: Job is waiting in the queue to be processed
    - **in_progress**: Job is currently being processed by a worker
    - **completed**: Job has finished successfully
    - **failed**: Job encountered an error during processing
    
    ## Notes
    
    - Job payload is returned as-is from the database
    - Timestamps are in ISO 8601 format with timezone information
    - Job retry count shows how many times the job has been retried
    - Callback retry count shows how many times callback delivery was attempted
    - Updated timestamp is only present if the job has been modified
    """
    try:
        # User is already authenticated via middleware
        user = request.state.user
        
        # Validate job_id format (basic UUID validation)
        if not job_id or not validate_uuid(job_id):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid job_id format. Must be a valid UUID."
            )
        
        # Retrieve job from database
        job_data = await get_job_by_id(job_id, user['email'])
        
        if not job_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job with ID '{job_id}' not found"
            )
        
        return JobStatusResponse(**job_data)
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve job: {str(e)}"
        )

@router.get("/jobs", response_model=JobListResponse)
async def list_jobs(
    request: Request,
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    limit: int = Query(20, ge=1, le=100, description="Number of jobs per page"),
    status: Optional[str] = Query(None, description="Filter by job status"),
    task_type: Optional[str] = Query(None, description="Filter by task type")
):
    """
    List all jobs with pagination and filtering.
    
    This endpoint returns a paginated list of jobs with optional filtering by status and task type.
    
    ## Query Parameters
    
    - **page** (integer, optional): Page number (default: 1, minimum: 1)
    - **limit** (integer, optional): Number of jobs per page (default: 20, minimum: 1, maximum: 100)
    - **status** (string, optional): Filter by job status (queued, in_progress, completed, failed)
    - **task_type** (string, optional): Filter by task type
    
    ## Response
    
    Returns a paginated list of jobs:
    
    - **jobs** (array): List of job items with basic information
    - **pagination** (object): Pagination information including:
      - **page**: Current page number
      - **limit**: Jobs per page
      - **total**: Total number of jobs
      - **pages**: Total number of pages
    
    ## Authentication
    
    Requires valid API key in header:
    - `X-API-Key: your_api_key_here`
    - `Authorization: Bearer your_api_key_here`
    
    ## Example Usage
    
    ```bash
    # Get first page of all jobs
    curl -X GET "http://localhost:8000/api/jobs" \\
         -H "X-API-Key: your_api_key"
    
    # Get completed jobs only
    curl -X GET "http://localhost:8000/api/jobs?status=completed" \\
         -H "X-API-Key: your_api_key"
    
    # Get email jobs with pagination
    curl -X GET "http://localhost:8000/api/jobs?task_type=email_send&page=2&limit=10" \\
         -H "X-API-Key: your_api_key"
    ```
    
    ## Example Response
    
    ```json
    {
      "jobs": [
        {
          "job_id": "123e4567-e89b-12d3-a456-426614174000",
          "task_type": "email_send",
          "status": "completed",
          "callback_url": "https://webhook.site/abc123",
          "retry_count": 0,
          "callback_retry_count": 0,
          "created_at": "2024-01-15T10:30:00Z",
          "updated_at": "2024-01-15T10:30:05Z"
        }
      ],
      "pagination": {
        "page": 1,
        "limit": 20,
        "total": 1,
        "pages": 1
      }
    }
    ```
    
    ## Error Responses
    
    - **401 Unauthorized**: Missing or invalid API key
    - **422 Unprocessable Content**: Invalid query parameters
    - **500 Internal Server Error**: Database or server errors
    """
    try:
        # User is already authenticated via middleware
        user = request.state.user
        
        # Validate status filter if provided
        if status and status not in ['queued', 'in_progress', 'completed', 'failed']:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid status filter. Must be one of: queued, in_progress, completed, failed"
            )
        
        # Get jobs list from database
        jobs_data = await get_jobs_list(page, limit, status, task_type, user['email'])
        
        return JobListResponse(**jobs_data)
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve jobs list: {str(e)}"
        )

@router.get("/dead-letter-queue", response_model=DeadLetterListResponse)
async def list_dead_letter_jobs(
    request: Request,
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    limit: int = Query(20, ge=1, le=100, description="Number of jobs per page"),
    task_type: Optional[str] = Query(None, description="Filter by task type")
):
    """
    List all jobs in the Redis dead letter queue with pagination and filtering.
    
    This endpoint returns a paginated list of jobs that have failed processing
    and are stored in the Redis dead letter queue for inspection and potential retry.
    
    ## Query Parameters
    
    - **page** (integer, optional): Page number (default: 1, minimum: 1)
    - **limit** (integer, optional): Number of jobs per page (default: 20, minimum: 1, maximum: 100)
    - **task_type** (string, optional): Filter by task type
    
    ## Response
    
    Returns a paginated list of dead letter jobs:
    
    - **jobs** (array): List of dead letter job items with failure information
    - **pagination** (object): Pagination information including:
      - **page**: Current page number
      - **limit**: Jobs per page
      - **total**: Total number of dead letter jobs
      - **pages**: Total number of pages
    
    ## Authentication
    
    Requires valid API key in header:
    - `X-API-Key: your_api_key_here`
    - `Authorization: Bearer your_api_key_here`
    
    ## Example Usage
    
    ```bash
    # Get first page of all dead letter jobs
    curl -X GET "http://localhost:8001/api/dead-letter-queue" \\
         -H "X-API-Key: your_api_key"
    
    # Get dead letter jobs for specific task type
    curl -X GET "http://localhost:8001/api/dead-letter-queue?task_type=data_transform" \\
         -H "X-API-Key: your_api_key"
    ```
    
    ## Example Response
    
    ```json
    {
      "jobs": [
        {
          "dlq_id": "dlq_123456",
          "job_id": "123e4567-e89b-12d3-a456-426614174000",
          "task_type": "data_transform",
          "payload": {"input": "data"},
          "error_message": "Invalid input format",
          "retry_count": 2,
          "max_retries": 3,
          "created_at": "2024-01-15T10:30:00Z",
          "updated_at": "2024-01-15T10:35:00Z"
        }
      ],
      "pagination": {
        "page": 1,
        "limit": 20,
        "total": 1,
        "pages": 1
      }
    }
    ```
    
    ## Error Responses
    
    - **401 Unauthorized**: Missing or invalid API key
    - **422 Unprocessable Content**: Invalid query parameters
    - **500 Internal Server Error**: Redis or server errors
    """
    try:
        # User is already authenticated via middleware
        user = request.state.user
        
        # Get dead letter jobs list from Redis
        jobs_data = await get_dead_letter_jobs(page, limit, task_type)
        
        return DeadLetterListResponse(**jobs_data)
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve dead letter jobs list: {str(e)}"
        )

@router.post("/dead-letter-queue/{dlq_id}/retry")
async def retry_dead_letter_job_endpoint(dlq_id: str, request: Request):
    """
    Retry a job from the Redis dead letter queue.
    
    This endpoint moves a failed job from the Redis dead letter queue back to the main
    processing queue for retry, if it hasn't exceeded the maximum retry count.
    
    ## Path Parameters
    
    - **dlq_id** (string, required): The dead letter queue job ID (e.g., "dlq_123456")
    
    ## Response
    
    Returns success status:
    
    - **success** (boolean): Whether the retry was successful
    - **message** (string): Success or error message
    
    ## Authentication
    
    Requires valid API key in header:
    - `X-API-Key: your_api_key_here`
    - `Authorization: Bearer your_api_key_here`
    
    ## Example Usage
    
    ```bash
    curl -X POST "http://localhost:8001/api/dead-letter-queue/dlq_123456/retry" \\
         -H "X-API-Key: your_api_key"
    ```
    
    ## Example Response
    
    ```json
    {
      "success": true,
      "message": "Job successfully moved back to processing queue"
    }
    ```
    
    ## Error Responses
    
    - **401 Unauthorized**: Missing or invalid API key
    - **404 Not Found**: Dead letter job with specified ID not found
    - **422 Unprocessable Content**: Invalid dlq_id format
    - **500 Internal Server Error**: Redis or server errors
    """
    try:
        # User is already authenticated via middleware
        user = request.state.user
        
        # Retry the dead letter job
        success = await retry_dead_letter_job(dlq_id)
        
        if success:
            return {
                "success": True,
                "message": "Job successfully moved back to processing queue"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dead letter job with ID '{dlq_id}' not found or has exceeded maximum retry count"
            )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retry dead letter job: {str(e)}"
        )

@router.get("/dead-letter-queue/stats")
async def get_dead_letter_queue_stats_endpoint(request: Request):
    """
    Get statistics about the Redis dead letter queue.
    
    This endpoint returns statistics about jobs in the dead letter queue,
    including total count and breakdown by task type.
    
    ## Response
    
    Returns dead letter queue statistics:
    
    - **total_jobs** (integer): Total number of jobs in dead letter queue
    - **task_type_breakdown** (object): Count of jobs by task type
    - **queue_name** (string): Name of the Redis queue
    
    ## Authentication
    
    Requires valid API key in header:
    - `X-API-Key: your_api_key_here`
    - `Authorization: Bearer your_api_key_here`
    
    ## Example Usage
    
    ```bash
    curl -X GET "http://localhost:8001/api/dead-letter-queue/stats" \\
         -H "X-API-Key: your_api_key"
    ```
    
    ## Example Response
    
    ```json
    {
      "total_jobs": 5,
      "task_type_breakdown": {
        "data_transform": 2,
        "http_call": 2,
        "email_send": 1
      },
      "queue_name": "dead_letter_queue"
    }
    ```
    
    ## Error Responses
    
    - **401 Unauthorized**: Missing or invalid API key
    - **500 Internal Server Error**: Redis or server errors
    """
    try:
        # User is already authenticated via middleware
        user = request.state.user
        
        # Get dead letter queue statistics from Redis
        stats = await get_dead_letter_queue_stats()
        
        return stats
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dead letter queue stats: {str(e)}"
        )
