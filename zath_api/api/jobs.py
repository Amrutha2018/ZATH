"""
Jobs API - Self-sufficient implementation
Contains models, validation, database operations, and endpoints
"""
from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel, HttpUrl, validator, Field
from typing import Dict, Any, Optional
import asyncpg
import json
from datetime import datetime
from db.connection import get_pool

router = APIRouter(tags=["Jobs"])

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
