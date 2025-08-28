"""
Jobs API - Self-sufficient implementation
Contains models, validation, database operations, and endpoints
"""
from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel, HttpUrl, validator, Field
from typing import Dict, Any, Optional
import asyncpg
import json
import uuid
from datetime import datetime
from db.connection import get_pool
from config.redis import get_redis_client

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
        return v.strip()

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
        retry_count: Number of retry attempts made
    """
    job_id: str = Field(..., description="Unique identifier for the job (UUID)")
    task_type: str = Field(..., description="Type of job being executed")
    status: str = Field(..., description="Current job status (queued, in_progress, completed, failed)")
    payload: Optional[Dict[str, Any]] = Field(None, description="Job payload data")
    callback_url: Optional[str] = Field(None, description="Webhook URL for notifications")
    created_at: str = Field(..., description="ISO timestamp when job was created")
    updated_at: Optional[str] = Field(None, description="ISO timestamp when job was last updated")
    retry_count: int = Field(..., description="Number of retry attempts made")

# Database Operations (self-contained)
async def create_job_in_db(task_type: str, payload: dict, callback_url: str = None) -> str:
    """Create a new job in the database and return job_id"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        job_id = await conn.fetchval(
            """
            INSERT INTO jobs (id, task_type, payload, callback_url, status)
            VALUES (gen_random_uuid(), $1, $2, $3, 'queued')
            RETURNING id
            """,
            task_type, json.dumps(payload), str(callback_url) if callback_url else None
        )
        return str(job_id)

async def get_job_by_id(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a job by its ID from the database.
    
    Args:
        job_id: The UUID of the job to retrieve
        
    Returns:
        Job data as dictionary or None if not found
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        job = await conn.fetchrow(
            """
            SELECT id, task_type, payload, callback_url, status, 
                   retry_count, created_at, updated_at
            FROM jobs 
            WHERE id = $1
            """,
            job_id
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
                "created_at": job['created_at'].isoformat() if job['created_at'] else None,
                "updated_at": job['updated_at'].isoformat() if job['updated_at'] else None
            }
        return None

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
            job_data.callback_url
        )
        
        # Push job to Redis queue
        try:
            job_queue_data = {
                "job_id": job_id,
                "task_type": job_data.task_type,
                "payload": job_data.payload,
                "callback_url": str(job_data.callback_url) if job_data.callback_url else None,
                "created_at": datetime.utcnow().isoformat()
            }
            
            redis_client = await get_redis_client()
            await redis_client.lpush("job_queue", json.dumps(job_queue_data))
        except Exception as redis_error:
            # Log Redis error but don't fail the job creation
            # The job is already in the database and can be processed later
            print(f"Warning: Failed to push job to Redis queue: {redis_error}")
            # In production, you might want to log this to a proper logging system
        
        return JobResponse(
            job_id=job_id,
            status="queued",
            created_at=datetime.utcnow().isoformat()
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
    - **retry_count** (integer): Number of retry attempts made
    
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
      "retry_count": 0
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
    - Retry count shows how many times the job has been retried
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
        job_data = await get_job_by_id(job_id)
        
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
