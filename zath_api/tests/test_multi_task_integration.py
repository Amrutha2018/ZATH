"""
Integration tests for multi-task support in ZATH system.

This module tests the complete workflow of creating, processing, and managing
jobs with different task types, including dead letter queue functionality.
"""

import asyncio
import json
import pytest
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

# Import the modules we need to test
from api.jobs import (
    create_job_in_db, get_job_by_id, get_jobs_list,
    add_to_dead_letter_queue, get_dead_letter_jobs, retry_dead_letter_job
)
from workers.task_handlers import execute_task, TASK_HANDLERS
from db.connection import get_pool, init_db_pool
from config.redis import get_redis_client


class TestMultiTaskIntegration:
    """Integration tests for multi-task support."""
    
    @pytest.fixture(autouse=True)
    async def setup_and_cleanup(self):
        """Set up database connection and clean up after tests."""
        await init_db_pool()
        yield
        # Cleanup is handled by the test framework
    
    @pytest.mark.asyncio
    async def test_http_call_task_workflow(self):
        """Test complete workflow for HTTP call tasks."""
        # Create a job
        job_id = await create_job_in_db(
            task_type="http_call",
            payload={
                "url": "https://example.com/api",
                "method": "POST",
                "headers": {"Content-Type": "application/json"},
                "data": {"test": "data"}
            },
            callback_url="https://webhook.site/test",
            user_email="test@example.com"
        )
        
        assert job_id is not None
        
        # Verify job was created
        job = await get_job_by_id(job_id, "test@example.com")
        assert job is not None
        assert job["task_type"] == "http_call"
        assert job["status"] == "queued"
        
        # Test task execution
        success, result, error = await execute_task("http_call", job["payload"])
        assert success is True
        assert "status" in result
        assert result["status"] == "success"
        assert "url" in result
        assert "method" in result
    
    @pytest.mark.asyncio
    async def test_data_transform_task_workflow(self):
        """Test complete workflow for data transformation tasks."""
        # Test flatten_json operation
        job_id = await create_job_in_db(
            task_type="data_transform",
            payload={
                "operation": "flatten_json",
                "data": {
                    "user": {
                        "name": "John",
                        "details": {"age": 25, "active": True}
                    }
                }
            },
            user_email="test@example.com"
        )
        
        assert job_id is not None
        
        # Verify job was created
        job = await get_job_by_id(job_id, "test@example.com")
        assert job is not None
        assert job["task_type"] == "data_transform"
        
        # Test task execution
        success, result, error = await execute_task("data_transform", job["payload"])
        assert success is True
        assert "result" in result
        assert "user.name" in result["result"]
        assert "user.details.age" in result["result"]
        assert result["result"]["user.name"] == "John"
        assert result["result"]["user.details.age"] == 25
    
    @pytest.mark.asyncio
    async def test_csv_to_json_operation(self):
        """Test CSV to JSON transformation."""
        csv_content = "name,age,city\nJohn,25,NYC\nJane,30,LA"
        
        success, result, error = await execute_task("data_transform", {
            "operation": "csv_to_json",
            "csv_content": csv_content,
            "delimiter": ","
        })
        
        assert success is True
        assert "result" in result
        assert len(result["result"]) == 2
        assert result["result"][0]["name"] == "John"
        assert result["result"][0]["age"] == "25"
        assert result["result"][1]["name"] == "Jane"
        assert result["result"][1]["age"] == "30"
    
    @pytest.mark.asyncio
    async def test_filter_records_operation(self):
        """Test record filtering operation."""
        records = [
            {"name": "John", "age": 25, "city": "NYC"},
            {"name": "Jane", "age": 30, "city": "LA"},
            {"name": "Bob", "age": 25, "city": "Chicago"}
        ]
        
        success, result, error = await execute_task("data_transform", {
            "operation": "filter_records",
            "records": records,
            "criteria": {"age": 25}
        })
        
        assert success is True
        assert "result" in result
        assert len(result["result"]) == 2
        assert all(record["age"] == 25 for record in result["result"])
    
    @pytest.mark.asyncio
    async def test_aggregate_operation(self):
        """Test data aggregation operation."""
        records = [
            {"value": 10},
            {"value": 20},
            {"value": 30}
        ]
        
        success, result, error = await execute_task("data_transform", {
            "operation": "aggregate",
            "records": records,
            "field": "value",
            "agg_type": "sum"
        })
        
        assert success is True
        assert "result" in result
        assert result["result"] == 60.0
    
    @pytest.mark.asyncio
    async def test_email_send_task(self):
        """Test email sending task."""
        success, result, error = await execute_task("email_send", {
            "to": "user@example.com",
            "subject": "Test Email",
            "body": "This is a test email"
        })
        
        assert success is True
        assert "to" in result
        assert result["to"] == "user@example.com"
        assert "message_id" in result
    
    @pytest.mark.asyncio
    async def test_webhook_call_task(self):
        """Test webhook call task."""
        success, result, error = await execute_task("webhook_call", {
            "url": "https://webhook.site/test",
            "method": "POST",
            "data": {"event": "test"}
        })
        
        assert success is True
        assert "url" in result
        assert result["url"] == "https://webhook.site/test"
        assert "method" in result
        assert result["method"] == "POST"
    
    @pytest.mark.asyncio
    async def test_file_upload_task(self):
        """Test file upload task."""
        success, result, error = await execute_task("file_upload", {
            "file_path": "/tmp/test.txt",
            "destination": "storage/uploads/",
            "file_size": 1024
        })
        
        assert success is True
        assert "file_path" in result
        assert result["file_path"] == "/tmp/test.txt"
        assert "upload_id" in result
    
    @pytest.mark.asyncio
    async def test_report_generate_task(self):
        """Test report generation task."""
        success, result, error = await execute_task("report_generate", {
            "report_type": "summary",
            "data_source": "database",
            "format": "pdf"
        })
        
        assert success is True
        assert "report_type" in result
        assert result["report_type"] == "summary"
        assert "report_id" in result
    
    @pytest.mark.asyncio
    async def test_unknown_task_type_handling(self):
        """Test handling of unknown task types."""
        success, result, error = await execute_task("unknown_task", {"test": "data"})
        
        assert success is False
        assert error is not None
        assert "Unknown task type" in error
    
    @pytest.mark.asyncio
    async def test_invalid_data_transform_operation(self):
        """Test handling of invalid data transformation operations."""
        success, result, error = await execute_task("data_transform", {
            "operation": "invalid_operation",
            "data": {"test": "data"}
        })
        
        assert success is False
        assert error is not None
        assert "Unknown operation" in error
    
    @pytest.mark.asyncio
    async def test_missing_required_payload_fields(self):
        """Test handling of missing required payload fields."""
        # Test missing operation for data_transform
        success, result, error = await execute_task("data_transform", {
            "data": {"test": "data"}
        })
        
        assert success is False
        assert error is not None
        assert "Missing 'operation'" in error
        
        # Test missing to for email_send
        success, result, error = await execute_task("email_send", {
            "subject": "Test",
            "body": "Test body"
        })
        
        assert success is False
        assert error is not None
        assert "Missing 'to' email address" in error
    
    @pytest.mark.asyncio
    async def test_dead_letter_queue_functionality(self):
        """Test dead letter queue functionality."""
        # Create a job that will fail
        job_id = str(uuid.uuid4())
        
        # Add to dead letter queue
        dlq_id = await add_to_dead_letter_queue(
            job_id=job_id,
            task_type="data_transform",
            payload={"operation": "invalid_operation"},
            error_message="Unknown operation: invalid_operation",
            retry_count=0,
            max_retries=3
        )
        
        assert dlq_id is not None
        
        # Retrieve dead letter jobs
        dlq_jobs = await get_dead_letter_jobs(page=1, limit=10)
        assert "jobs" in dlq_jobs
        assert len(dlq_jobs["jobs"]) >= 1
        
        # Find our job in the dead letter queue
        our_job = None
        for job in dlq_jobs["jobs"]:
            if job["job_id"] == job_id:
                our_job = job
                break
        
        assert our_job is not None
        assert our_job["task_type"] == "data_transform"
        assert our_job["error_message"] == "Unknown operation: invalid_operation"
        assert our_job["retry_count"] == 0
        assert our_job["max_retries"] == 3
    
    @pytest.mark.asyncio
    async def test_dead_letter_queue_retry_functionality(self):
        """Test retrying jobs from dead letter queue."""
        # Create a job that will fail
        job_id = str(uuid.uuid4())
        
        # Add to dead letter queue
        dlq_id = await add_to_dead_letter_queue(
            job_id=job_id,
            task_type="http_call",
            payload={"url": "https://example.com"},
            error_message="Connection timeout",
            retry_count=0,
            max_retries=3
        )
        
        # Retry the job
        success = await retry_dead_letter_job(dlq_id)
        assert success is True
        
        # Verify retry count was updated
        dlq_jobs = await get_dead_letter_jobs(page=1, limit=10)
        our_job = None
        for job in dlq_jobs["jobs"]:
            if job["job_id"] == job_id:
                our_job = job
                break
        
        assert our_job is not None
        assert our_job["retry_count"] == 1
    
    @pytest.mark.asyncio
    async def test_dead_letter_queue_max_retries(self):
        """Test dead letter queue max retries functionality."""
        # Create a job that has exceeded max retries
        job_id = str(uuid.uuid4())
        
        # Add to dead letter queue with max retries exceeded
        dlq_id = await add_to_dead_letter_queue(
            job_id=job_id,
            task_type="http_call",
            payload={"url": "https://example.com"},
            error_message="Connection timeout",
            retry_count=3,
            max_retries=3
        )
        
        # Try to retry the job (should fail)
        success = await retry_dead_letter_job(dlq_id)
        assert success is False
    
    @pytest.mark.asyncio
    async def test_job_listing_with_task_type_filter(self):
        """Test job listing with task type filtering."""
        # Create jobs of different types
        http_job_id = await create_job_in_db(
            task_type="http_call",
            payload={"url": "https://example.com"},
            user_email="test@example.com"
        )
        
        email_job_id = await create_job_in_db(
            task_type="email_send",
            payload={"to": "test@example.com", "subject": "Test"},
            user_email="test@example.com"
        )
        
        # Get all jobs
        all_jobs = await get_jobs_list(page=1, limit=10, user_email="test@example.com")
        assert len(all_jobs["jobs"]) >= 2
        
        # Filter by task type
        http_jobs = await get_jobs_list(page=1, limit=10, task_type="http_call", user_email="test@example.com")
        assert len(http_jobs["jobs"]) >= 1
        assert all(job["task_type"] == "http_call" for job in http_jobs["jobs"])
        
        email_jobs = await get_jobs_list(page=1, limit=10, task_type="email_send", user_email="test@example.com")
        assert len(email_jobs["jobs"]) >= 1
        assert all(job["task_type"] == "email_send" for job in email_jobs["jobs"])
    
    @pytest.mark.asyncio
    async def test_task_type_validation(self):
        """Test task type validation in job creation."""
        # Test valid task types
        valid_task_types = ["http_call", "data_transform", "email_send", "webhook_call", "file_upload", "report_generate"]
        
        for task_type in valid_task_types:
            job_id = await create_job_in_db(
                task_type=task_type,
                payload={"test": "data"},
                user_email="test@example.com"
            )
            assert job_id is not None
            
            # Verify job was created with correct task type
            job = await get_job_by_id(job_id, "test@example.com")
            assert job["task_type"] == task_type
    
    @pytest.mark.asyncio
    async def test_all_task_handlers_registered(self):
        """Test that all task handlers are properly registered."""
        expected_handlers = {
            'http_call', 'data_transform', 'email_send', 
            'webhook_call', 'file_upload', 'report_generate'
        }
        
        assert set(TASK_HANDLERS.keys()) == expected_handlers
        
        # Test that all handlers are callable
        for task_type, handler in TASK_HANDLERS.items():
            assert callable(handler), f"Handler for {task_type} is not callable"
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow for different task types."""
        # Test data transformation workflow
        transform_job_id = await create_job_in_db(
            task_type="data_transform",
            payload={
                "operation": "flatten_json",
                "data": {"nested": {"value": 42}}
            },
            user_email="test@example.com"
        )
        
        # Execute the task
        job = await get_job_by_id(transform_job_id, "test@example.com")
        success, result, error = await execute_task("data_transform", job["payload"])
        
        assert success is True
        assert "nested.value" in result["result"]
        assert result["result"]["nested.value"] == 42
        
        # Test email workflow
        email_job_id = await create_job_in_db(
            task_type="email_send",
            payload={
                "to": "recipient@example.com",
                "subject": "Test Subject",
                "body": "Test Body"
            },
            user_email="test@example.com"
        )
        
        # Execute the task
        job = await get_job_by_id(email_job_id, "test@example.com")
        success, result, error = await execute_task("email_send", job["payload"])
        
        assert success is True
        assert result["to"] == "recipient@example.com"
        assert "message_id" in result
