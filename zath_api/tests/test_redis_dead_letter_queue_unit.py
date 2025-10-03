"""
Unit tests for Redis dead letter queue functionality.

This module tests the dead letter queue functions without requiring
Redis to be running (mocks Redis operations).
"""

import pytest
import json
from unittest.mock import AsyncMock, patch
from workers.dead_letter_queue import (
    add_to_dead_letter_queue,
    get_dead_letter_jobs,
    retry_dead_letter_job,
    get_dead_letter_queue_stats,
    remove_dead_letter_job
)


class TestRedisDeadLetterQueue:
    """Unit tests for Redis dead letter queue."""
    
    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client for testing."""
        mock_client = AsyncMock()
        mock_client.lpush = AsyncMock()
        mock_client.hset = AsyncMock()
        mock_client.expire = AsyncMock()
        mock_client.lrange = AsyncMock()
        mock_client.lrem = AsyncMock()
        mock_client.llen = AsyncMock()
        mock_client.delete = AsyncMock()
        return mock_client
    
    @pytest.mark.asyncio
    async def test_add_to_dead_letter_queue(self, mock_redis_client):
        """Test adding a job to dead letter queue."""
        with patch('workers.dead_letter_queue.get_redis_client', return_value=mock_redis_client):
            job_id = "test-job-123"
            task_type = "http_call"
            payload = {"url": "https://example.com"}
            error_message = "Connection timeout"
            
            result = await add_to_dead_letter_queue(
                job_id=job_id,
                task_type=task_type,
                payload=payload,
                error_message=error_message,
                retry_count=0,
                max_retries=3
            )
            
            # Verify Redis operations were called
            mock_redis_client.lpush.assert_called_once()
            mock_redis_client.hset.assert_called_once()
            mock_redis_client.expire.assert_called_once()
            
            # Verify the job data was stored correctly
            lpush_args = mock_redis_client.lpush.call_args
            assert lpush_args[0][0] == "dead_letter_queue"
            
            job_data = json.loads(lpush_args[0][1])
            assert job_data["job_id"] == job_id
            assert job_data["task_type"] == task_type
            assert job_data["payload"] == payload
            assert job_data["error_message"] == error_message
            assert job_data["retry_count"] == 0
            assert job_data["max_retries"] == 3
    
    @pytest.mark.asyncio
    async def test_get_dead_letter_jobs(self, mock_redis_client):
        """Test retrieving dead letter jobs."""
        # Mock Redis response
        mock_jobs_data = [
            json.dumps({
                "job_id": "job-1",
                "task_type": "http_call",
                "payload": {"url": "https://example.com"},
                "error_message": "Connection timeout",
                "retry_count": 0,
                "max_retries": 3,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }),
            json.dumps({
                "job_id": "job-2",
                "task_type": "data_transform",
                "payload": {"operation": "flatten_json"},
                "error_message": "Invalid data format",
                "retry_count": 1,
                "max_retries": 3,
                "created_at": "2024-01-15T10:25:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            })
        ]
        
        mock_redis_client.lrange.return_value = mock_jobs_data
        
        with patch('workers.dead_letter_queue.get_redis_client', return_value=mock_redis_client):
            result = await get_dead_letter_jobs(page=1, limit=10)
            
            # Verify Redis operation was called
            mock_redis_client.lrange.assert_called_once_with("dead_letter_queue", 0, -1)
            
            # Verify result structure
            assert "jobs" in result
            assert "pagination" in result
            assert len(result["jobs"]) == 2
            assert result["pagination"]["total"] == 2
            assert result["pagination"]["page"] == 1
            assert result["pagination"]["limit"] == 10
            
            # Verify job data
            job1 = result["jobs"][0]  # Should be sorted by created_at desc
            assert job1["job_id"] == "job-1"
            assert job1["task_type"] == "http_call"
            assert "dlq_id" in job1
    
    @pytest.mark.asyncio
    async def test_get_dead_letter_jobs_with_filter(self, mock_redis_client):
        """Test retrieving dead letter jobs with task type filter."""
        mock_jobs_data = [
            json.dumps({
                "job_id": "job-1",
                "task_type": "http_call",
                "payload": {"url": "https://example.com"},
                "error_message": "Connection timeout",
                "retry_count": 0,
                "max_retries": 3,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }),
            json.dumps({
                "job_id": "job-2",
                "task_type": "data_transform",
                "payload": {"operation": "flatten_json"},
                "error_message": "Invalid data format",
                "retry_count": 1,
                "max_retries": 3,
                "created_at": "2024-01-15T10:25:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            })
        ]
        
        mock_redis_client.lrange.return_value = mock_jobs_data
        
        with patch('workers.dead_letter_queue.get_redis_client', return_value=mock_redis_client):
            result = await get_dead_letter_jobs(page=1, limit=10, task_type="http_call")
            
            # Should only return http_call jobs
            assert len(result["jobs"]) == 1
            assert result["jobs"][0]["task_type"] == "http_call"
    
    @pytest.mark.asyncio
    async def test_retry_dead_letter_job_success(self, mock_redis_client):
        """Test successfully retrying a dead letter job."""
        # Mock Redis responses
        mock_jobs_data = [
            json.dumps({
                "job_id": "job-1",
                "task_type": "http_call",
                "payload": {"url": "https://example.com"},
                "error_message": "Connection timeout",
                "retry_count": 0,
                "max_retries": 3,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            })
        ]
        
        mock_redis_client.lrange.return_value = mock_jobs_data
        mock_redis_client.lpush = AsyncMock()
        mock_redis_client.lrem = AsyncMock()
        mock_redis_client.hset = AsyncMock()
        
        with patch('workers.dead_letter_queue.get_redis_client', return_value=mock_redis_client):
            # Calculate the expected dlq_id
            expected_dlq_id = f"dlq_{hash(mock_jobs_data[0]) % 1000000}"
            
            result = await retry_dead_letter_job(expected_dlq_id)
            
            # Verify result
            assert result is True
            
            # Verify Redis operations
            mock_redis_client.lpush.assert_called_once()  # Move to main queue
            mock_redis_client.lrem.assert_called_once()   # Remove from DLQ
            mock_redis_client.hset.assert_called_once()   # Update metadata
    
    @pytest.mark.asyncio
    async def test_retry_dead_letter_job_max_retries_exceeded(self, mock_redis_client):
        """Test retrying a job that has exceeded max retries."""
        mock_jobs_data = [
            json.dumps({
                "job_id": "job-1",
                "task_type": "http_call",
                "payload": {"url": "https://example.com"},
                "error_message": "Connection timeout",
                "retry_count": 3,  # Already at max retries
                "max_retries": 3,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            })
        ]
        
        mock_redis_client.lrange.return_value = mock_jobs_data
        
        with patch('workers.dead_letter_queue.get_redis_client', return_value=mock_redis_client):
            expected_dlq_id = f"dlq_{hash(mock_jobs_data[0]) % 1000000}"
            
            result = await retry_dead_letter_job(expected_dlq_id)
            
            # Should fail because max retries exceeded
            assert result is False
    
    @pytest.mark.asyncio
    async def test_retry_dead_letter_job_not_found(self, mock_redis_client):
        """Test retrying a non-existent dead letter job."""
        mock_redis_client.lrange.return_value = []
        
        with patch('workers.dead_letter_queue.get_redis_client', return_value=mock_redis_client):
            result = await retry_dead_letter_job("dlq_999999")
            
            # Should fail because job not found
            assert result is False
    
    @pytest.mark.asyncio
    async def test_remove_dead_letter_job(self, mock_redis_client):
        """Test removing a job from dead letter queue."""
        mock_jobs_data = [
            json.dumps({
                "job_id": "job-1",
                "task_type": "http_call",
                "payload": {"url": "https://example.com"},
                "error_message": "Connection timeout",
                "retry_count": 0,
                "max_retries": 3,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            })
        ]
        
        mock_redis_client.lrange.return_value = mock_jobs_data
        mock_redis_client.lrem = AsyncMock()
        mock_redis_client.delete = AsyncMock()
        
        with patch('workers.dead_letter_queue.get_redis_client', return_value=mock_redis_client):
            expected_dlq_id = f"dlq_{hash(mock_jobs_data[0]) % 1000000}"
            
            result = await remove_dead_letter_job(expected_dlq_id)
            
            # Verify result
            assert result is True
            
            # Verify Redis operations
            mock_redis_client.lrem.assert_called_once()   # Remove from DLQ
            mock_redis_client.delete.assert_called_once() # Remove metadata
    
    @pytest.mark.asyncio
    async def test_get_dead_letter_queue_stats(self, mock_redis_client):
        """Test getting dead letter queue statistics."""
        mock_jobs_data = [
            json.dumps({
                "job_id": "job-1",
                "task_type": "http_call",
                "payload": {"url": "https://example.com"},
                "error_message": "Connection timeout",
                "retry_count": 0,
                "max_retries": 3,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }),
            json.dumps({
                "job_id": "job-2",
                "task_type": "http_call",
                "payload": {"url": "https://example2.com"},
                "error_message": "Connection timeout",
                "retry_count": 1,
                "max_retries": 3,
                "created_at": "2024-01-15T10:25:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }),
            json.dumps({
                "job_id": "job-3",
                "task_type": "data_transform",
                "payload": {"operation": "flatten_json"},
                "error_message": "Invalid data format",
                "retry_count": 0,
                "max_retries": 3,
                "created_at": "2024-01-15T10:20:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            })
        ]
        
        mock_redis_client.llen.return_value = 3
        mock_redis_client.lrange.return_value = mock_jobs_data
        
        with patch('workers.dead_letter_queue.get_redis_client', return_value=mock_redis_client):
            result = await get_dead_letter_queue_stats()
            
            # Verify result structure
            assert "total_jobs" in result
            assert "task_type_breakdown" in result
            assert "queue_name" in result
            
            # Verify counts
            assert result["total_jobs"] == 3
            assert result["task_type_breakdown"]["http_call"] == 2
            assert result["task_type_breakdown"]["data_transform"] == 1
            assert result["queue_name"] == "dead_letter_queue"
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_json(self, mock_redis_client):
        """Test error handling for invalid JSON in dead letter queue."""
        # Mock Redis response with invalid JSON
        mock_jobs_data = [
            "invalid json data",
            json.dumps({
                "job_id": "job-1",
                "task_type": "http_call",
                "payload": {"url": "https://example.com"},
                "error_message": "Connection timeout",
                "retry_count": 0,
                "max_retries": 3,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            })
        ]
        
        mock_redis_client.lrange.return_value = mock_jobs_data
        
        with patch('workers.dead_letter_queue.get_redis_client', return_value=mock_redis_client):
            result = await get_dead_letter_jobs(page=1, limit=10)
            
            # Should handle invalid JSON gracefully and return valid jobs
            assert len(result["jobs"]) == 1
            assert result["jobs"][0]["job_id"] == "job-1"
    
    @pytest.mark.asyncio
    async def test_pagination(self, mock_redis_client):
        """Test pagination functionality."""
        # Create 5 mock jobs
        mock_jobs_data = []
        for i in range(5):
            mock_jobs_data.append(json.dumps({
                "job_id": f"job-{i}",
                "task_type": "http_call",
                "payload": {"url": f"https://example{i}.com"},
                "error_message": f"Error {i}",
                "retry_count": 0,
                "max_retries": 3,
                "created_at": f"2024-01-15T10:{30-i}:00Z",
                "updated_at": f"2024-01-15T10:{30-i}:00Z"
            }))
        
        mock_redis_client.lrange.return_value = mock_jobs_data
        
        with patch('workers.dead_letter_queue.get_redis_client', return_value=mock_redis_client):
            # Test first page
            result_page1 = await get_dead_letter_jobs(page=1, limit=2)
            assert len(result_page1["jobs"]) == 2
            assert result_page1["pagination"]["page"] == 1
            assert result_page1["pagination"]["total"] == 5
            assert result_page1["pagination"]["pages"] == 3
            
            # Test second page
            result_page2 = await get_dead_letter_jobs(page=2, limit=2)
            assert len(result_page2["jobs"]) == 2
            assert result_page2["pagination"]["page"] == 2
            
            # Test third page (should have 1 job)
            result_page3 = await get_dead_letter_jobs(page=3, limit=2)
            assert len(result_page3["jobs"]) == 1
            assert result_page3["pagination"]["page"] == 3
