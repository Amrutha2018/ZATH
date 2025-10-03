"""
Unit tests for task handlers without database dependencies.

This module tests the task handlers in isolation to verify they work correctly
without requiring database connections.
"""

import pytest
from workers.task_handlers import execute_task, TASK_HANDLERS


class TestTaskHandlers:
    """Unit tests for task handlers."""
    
    @pytest.mark.asyncio
    async def test_http_call_handler(self):
        """Test HTTP call task handler."""
        payload = {
            "url": "https://example.com/api",
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "data": {"test": "data"}
        }
        
        success, result, error = await execute_task("http_call", payload)
        
        assert success is True
        assert error is None
        assert "status" in result
        assert result["status"] == "success"
        assert result["url"] == "https://example.com/api"
        assert result["method"] == "POST"
        assert "response_code" in result
        assert "response_time_ms" in result
    
    @pytest.mark.asyncio
    async def test_data_transform_flatten_json(self):
        """Test data transformation with flatten_json operation."""
        payload = {
            "operation": "flatten_json",
            "data": {
                "user": {
                    "name": "John",
                    "details": {"age": 25, "active": True}
                }
            }
        }
        
        success, result, error = await execute_task("data_transform", payload)
        
        assert success is True
        assert error is None
        assert "result" in result
        assert "user.name" in result["result"]
        assert "user.details.age" in result["result"]
        assert "user.details.active" in result["result"]
        assert result["result"]["user.name"] == "John"
        assert result["result"]["user.details.age"] == 25
        assert result["result"]["user.details.active"] is True
    
    @pytest.mark.asyncio
    async def test_data_transform_csv_to_json(self):
        """Test data transformation with csv_to_json operation."""
        csv_content = "name,age,city\nJohn,25,NYC\nJane,30,LA"
        payload = {
            "operation": "csv_to_json",
            "csv_content": csv_content,
            "delimiter": ","
        }
        
        success, result, error = await execute_task("data_transform", payload)
        
        assert success is True
        assert error is None
        assert "result" in result
        assert len(result["result"]) == 2
        assert result["result"][0]["name"] == "John"
        assert result["result"][0]["age"] == "25"
        assert result["result"][0]["city"] == "NYC"
        assert result["result"][1]["name"] == "Jane"
        assert result["result"][1]["age"] == "30"
        assert result["result"][1]["city"] == "LA"
        assert result["record_count"] == 2
    
    @pytest.mark.asyncio
    async def test_data_transform_filter_records(self):
        """Test data transformation with filter_records operation."""
        records = [
            {"name": "John", "age": 25, "city": "NYC"},
            {"name": "Jane", "age": 30, "city": "LA"},
            {"name": "Bob", "age": 25, "city": "Chicago"}
        ]
        payload = {
            "operation": "filter_records",
            "records": records,
            "criteria": {"age": 25}
        }
        
        success, result, error = await execute_task("data_transform", payload)
        
        assert success is True
        assert error is None
        assert "result" in result
        assert len(result["result"]) == 2
        assert all(record["age"] == 25 for record in result["result"])
        assert result["filtered_count"] == 2
        assert result["original_count"] == 3
    
    @pytest.mark.asyncio
    async def test_data_transform_aggregate(self):
        """Test data transformation with aggregate operation."""
        records = [
            {"value": 10},
            {"value": 20},
            {"value": 30}
        ]
        payload = {
            "operation": "aggregate",
            "records": records,
            "field": "value",
            "agg_type": "sum"
        }
        
        success, result, error = await execute_task("data_transform", payload)
        
        assert success is True
        assert error is None
        assert "result" in result
        assert result["result"] == 60.0
        assert result["field"] == "value"
        assert result["agg_type"] == "sum"
        assert result["record_count"] == 3
    
    @pytest.mark.asyncio
    async def test_email_send_handler(self):
        """Test email send task handler."""
        payload = {
            "to": "user@example.com",
            "subject": "Test Email",
            "body": "This is a test email"
        }
        
        success, result, error = await execute_task("email_send", payload)
        
        assert success is True
        assert error is None
        assert "to" in result
        assert result["to"] == "user@example.com"
        assert "subject" in result
        assert result["subject"] == "Test Email"
        assert "message_id" in result
        assert result["message_id"].startswith("msg_")
    
    @pytest.mark.asyncio
    async def test_webhook_call_handler(self):
        """Test webhook call task handler."""
        payload = {
            "url": "https://webhook.site/test",
            "method": "POST",
            "headers": {"Authorization": "Bearer token"},
            "data": {"event": "test"}
        }
        
        success, result, error = await execute_task("webhook_call", payload)
        
        assert success is True
        assert error is None
        assert "url" in result
        assert result["url"] == "https://webhook.site/test"
        assert "method" in result
        assert result["method"] == "POST"
        assert "response_code" in result
    
    @pytest.mark.asyncio
    async def test_file_upload_handler(self):
        """Test file upload task handler."""
        payload = {
            "file_path": "/tmp/test.txt",
            "destination": "storage/uploads/",
            "file_size": 1024
        }
        
        success, result, error = await execute_task("file_upload", payload)
        
        assert success is True
        assert error is None
        assert "file_path" in result
        assert result["file_path"] == "/tmp/test.txt"
        assert "destination" in result
        assert result["destination"] == "storage/uploads/"
        assert "upload_id" in result
        assert result["upload_id"].startswith("upload_")
    
    @pytest.mark.asyncio
    async def test_report_generate_handler(self):
        """Test report generation task handler."""
        payload = {
            "report_type": "summary",
            "data_source": "database",
            "format": "pdf"
        }
        
        success, result, error = await execute_task("report_generate", payload)
        
        assert success is True
        assert error is None
        assert "report_type" in result
        assert result["report_type"] == "summary"
        assert "data_source" in result
        assert result["data_source"] == "database"
        assert "format" in result
        assert result["format"] == "pdf"
        assert "report_id" in result
        assert result["report_id"].startswith("report_")
    
    @pytest.mark.asyncio
    async def test_unknown_task_type(self):
        """Test handling of unknown task types."""
        success, result, error = await execute_task("unknown_task", {"test": "data"})
        
        assert success is False
        assert result == {}
        assert error is not None
        assert "Unknown task type" in error
        assert "unknown_task" in error
    
    @pytest.mark.asyncio
    async def test_invalid_data_transform_operation(self):
        """Test handling of invalid data transformation operations."""
        payload = {
            "operation": "invalid_operation",
            "data": {"test": "data"}
        }
        
        success, result, error = await execute_task("data_transform", payload)
        
        assert success is False
        assert result == {}
        assert error is not None
        assert "Unknown operation" in error
        assert "invalid_operation" in error
    
    @pytest.mark.asyncio
    async def test_missing_operation_for_data_transform(self):
        """Test handling of missing operation for data_transform."""
        payload = {
            "data": {"test": "data"}
        }
        
        success, result, error = await execute_task("data_transform", payload)
        
        assert success is False
        assert result == {}
        assert error is not None
        assert "Missing 'operation'" in error
    
    @pytest.mark.asyncio
    async def test_missing_data_for_flatten_json(self):
        """Test handling of missing data for flatten_json operation."""
        payload = {
            "operation": "flatten_json"
        }
        
        success, result, error = await execute_task("data_transform", payload)
        
        # flatten_json with no data should succeed with empty dict
        assert success is True
        assert error is None
        assert "result" in result
        assert result["result"] == {}
    
    @pytest.mark.asyncio
    async def test_missing_csv_content_for_csv_to_json(self):
        """Test handling of missing csv_content for csv_to_json operation."""
        payload = {
            "operation": "csv_to_json",
            "delimiter": ","
        }
        
        success, result, error = await execute_task("data_transform", payload)
        
        assert success is False
        assert result == {}
        assert error is not None
        assert "Missing 'csv_content'" in error
    
    @pytest.mark.asyncio
    async def test_missing_records_for_filter_records(self):
        """Test handling of missing records for filter_records operation."""
        payload = {
            "operation": "filter_records",
            "criteria": {"age": 25}
        }
        
        success, result, error = await execute_task("data_transform", payload)
        
        assert success is False
        assert result == {}
        assert error is not None
        assert "Missing 'records'" in error
    
    @pytest.mark.asyncio
    async def test_missing_criteria_for_filter_records(self):
        """Test handling of missing criteria for filter_records operation."""
        payload = {
            "operation": "filter_records",
            "records": [{"name": "John", "age": 25}]
        }
        
        success, result, error = await execute_task("data_transform", payload)
        
        assert success is False
        assert result == {}
        assert error is not None
        assert "Missing 'criteria'" in error
    
    @pytest.mark.asyncio
    async def test_missing_field_for_aggregate(self):
        """Test handling of missing field for aggregate operation."""
        payload = {
            "operation": "aggregate",
            "records": [{"value": 10}],
            "agg_type": "sum"
        }
        
        success, result, error = await execute_task("data_transform", payload)
        
        assert success is False
        assert result == {}
        assert error is not None
        assert "Missing 'field'" in error
    
    @pytest.mark.asyncio
    async def test_missing_to_for_email_send(self):
        """Test handling of missing 'to' field for email_send."""
        payload = {
            "subject": "Test Subject",
            "body": "Test Body"
        }
        
        success, result, error = await execute_task("email_send", payload)
        
        assert success is False
        assert result == {}
        assert error is not None
        assert "Missing 'to' email address" in error
    
    @pytest.mark.asyncio
    async def test_missing_url_for_webhook_call(self):
        """Test handling of missing 'url' field for webhook_call."""
        payload = {
            "method": "POST",
            "data": {"test": "data"}
        }
        
        success, result, error = await execute_task("webhook_call", payload)
        
        assert success is False
        assert result == {}
        assert error is not None
        assert "Missing 'url' for webhook call" in error
    
    @pytest.mark.asyncio
    async def test_missing_file_path_for_file_upload(self):
        """Test handling of missing 'file_path' field for file_upload."""
        payload = {
            "destination": "storage/",
            "file_size": 1024
        }
        
        success, result, error = await execute_task("file_upload", payload)
        
        assert success is False
        assert result == {}
        assert error is not None
        assert "Missing 'file_path' for file upload" in error
    
    @pytest.mark.asyncio
    async def test_all_task_handlers_registered(self):
        """Test that all expected task handlers are registered."""
        expected_handlers = {
            'http_call', 'data_transform', 'email_send', 
            'webhook_call', 'file_upload', 'report_generate'
        }
        
        assert set(TASK_HANDLERS.keys()) == expected_handlers
        
        # Test that all handlers are callable
        for task_type, handler in TASK_HANDLERS.items():
            assert callable(handler), f"Handler for {task_type} is not callable"
    
    @pytest.mark.asyncio
    async def test_aggregate_different_operations(self):
        """Test aggregate operation with different aggregation types."""
        records = [{"value": 10}, {"value": 20}, {"value": 30}]
        
        # Test sum
        success, result, error = await execute_task("data_transform", {
            "operation": "aggregate",
            "records": records,
            "field": "value",
            "agg_type": "sum"
        })
        assert success is True
        assert result["result"] == 60.0
        
        # Test average
        success, result, error = await execute_task("data_transform", {
            "operation": "aggregate",
            "records": records,
            "field": "value",
            "agg_type": "avg"
        })
        assert success is True
        assert result["result"] == 20.0
        
        # Test min
        success, result, error = await execute_task("data_transform", {
            "operation": "aggregate",
            "records": records,
            "field": "value",
            "agg_type": "min"
        })
        assert success is True
        assert result["result"] == 10.0
        
        # Test max
        success, result, error = await execute_task("data_transform", {
            "operation": "aggregate",
            "records": records,
            "field": "value",
            "agg_type": "max"
        })
        assert success is True
        assert result["result"] == 30.0
    
    @pytest.mark.asyncio
    async def test_csv_to_json_different_delimiters(self):
        """Test CSV to JSON with different delimiters."""
        # Test semicolon delimiter
        csv_content = "name;age;city\nJohn;25;NYC\nJane;30;LA"
        success, result, error = await execute_task("data_transform", {
            "operation": "csv_to_json",
            "csv_content": csv_content,
            "delimiter": ";"
        })
        
        assert success is True
        assert len(result["result"]) == 2
        assert result["result"][0]["name"] == "John"
        assert result["result"][0]["age"] == "25"
        
        # Test tab delimiter
        csv_content = "name\tage\tcity\nJohn\t25\tNYC\nJane\t30\tLA"
        success, result, error = await execute_task("data_transform", {
            "operation": "csv_to_json",
            "csv_content": csv_content,
            "delimiter": "\t"
        })
        
        assert success is True
        assert len(result["result"]) == 2
        assert result["result"][0]["name"] == "John"
        assert result["result"][0]["age"] == "25"
